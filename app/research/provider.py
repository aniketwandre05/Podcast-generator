import io
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from app.sarvam.llm import generate_structured_json

logger = logging.getLogger("podcastai.research")

class BaseResearchProvider(ABC):
    @abstractmethod
    async def extract_text(self, source: str) -> str:
        pass

class DocumentResearchProvider(BaseResearchProvider):
    async def extract_text(self, file_path_or_content: str) -> str:
        """Extract text from local path or text content."""
        if not os.path.exists(file_path_or_content):
            return file_path_or_content # Already raw text

        path = file_path_or_content.lower()
        if path.endswith(".pdf"):
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path_or_content)
                text = " ".join([page.extract_text() or "" for page in reader.pages])
                return text
            except Exception as e:
                logger.error(f"Error reading PDF: {e}")
                return ""
        elif path.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(file_path_or_content)
                return " ".join([p.text for p in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error reading DOCX: {e}")
                return ""
        elif path.endswith((".txt", ".md")):
            with open(file_path_or_content, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        return ""

class WebUrlResearchProvider(BaseResearchProvider):
    async def extract_text(self, url: str) -> str:
        """Extract readable text from a web page."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PodcastAI/1.0"}
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return f"Could not retrieve URL content (status {resp.status_code})"

                soup = BeautifulSoup(resp.text, "html.parser")
                # Extract page title
                page_title = soup.title.string.strip() if soup.title and soup.title.string else url

                # Remove script and style elements
                for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    element.extract()
                
                text = soup.get_text(separator=" ", strip=True)
                clean_text = re.sub(r"\s+", " ", text).strip()
                return f"Title: {page_title}\n\nContent:\n{clean_text[:20000]}"
        except Exception as e:
            logger.error(f"URL extraction error for {url}: {e}")
            return f"Error extracting content from URL: {e}"

def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube 11-character video ID from varied URL formats."""
    patterns = [
        r"(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None

def is_youtube_url(url: str) -> bool:
    """Check if a URL points to YouTube."""
    return bool(extract_youtube_video_id(url))

class YouTubeResearchProvider(BaseResearchProvider):
    """Extracts metadata and full transcripts from YouTube videos without requiring an API key."""

    async def get_video_metadata(self, video_id: str) -> Dict[str, str]:
        """Fetch video title and channel/author using public YouTube oEmbed."""
        title = f"YouTube Video ({video_id})"
        author = "YouTube Creator"
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(oembed_url)
                if resp.status_code == 200:
                    meta = resp.json()
                    title = meta.get("title", title)
                    author = meta.get("author_name", author)
        except Exception as e:
            logger.warning(f"Could not fetch YouTube oEmbed metadata for {video_id}: {e}")
        return {"title": title, "author": author}

    def fetch_transcript_text(self, video_id: str) -> Optional[str]:
        """Fetch transcript text using youtube-transcript-api with multi-language fallback."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()

            # First attempt: priority Indian languages + English
            preferred_langs = ["en", "en-IN", "hi", "hi-IN", "ta", "te", "mr", "bn", "gu", "kn", "ml"]
            try:
                transcript_list = api.list(video_id)
                transcript = transcript_list.find_transcript(preferred_langs)
                data = transcript.fetch().to_raw_data()
            except Exception:
                # Second attempt: try fetch default or iterate any available transcript
                try:
                    data = api.fetch(video_id).to_raw_data()
                except Exception:
                    # Third attempt: try any transcript in the list
                    data = None
                    for t in api.list(video_id):
                        data = t.fetch().to_raw_data()
                        break

            if data:
                text_snippets = [entry.get("text", "") for entry in data if entry.get("text")]
                full_transcript = " ".join(text_snippets)
                return re.sub(r"\s+", " ", full_transcript).strip()
        except Exception as e:
            logger.warning(f"Transcript extraction failed for YouTube video {video_id}: {e}")

        return None

    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract full details, metadata, and transcript from a YouTube URL."""
        video_id = extract_youtube_video_id(url)
        if not video_id:
            return {
                "status": "error",
                "message": "Invalid YouTube URL format.",
                "url": url,
            }

        meta = await self.get_video_metadata(video_id)
        transcript = self.fetch_transcript_text(video_id)
        has_transcript = bool(transcript and len(transcript) > 50)

        content = (
            transcript
            if has_transcript
            else f"Video Title: {meta['title']} by {meta['author']}. Note: Automatic captions were unavailable on this video; topic research will synthesize around the title and themes."
        )

        words = len(content.split()) if content else 0

        return {
            "status": "success",
            "source_type": "youtube",
            "video_id": video_id,
            "title": meta["title"],
            "author": meta["author"],
            "url": url,
            "content": content,
            "has_transcript": has_transcript,
            "word_count": words,
        }

    async def extract_text(self, url: str) -> str:
        """Extract formatted research text from a YouTube video."""
        info = await self.extract_info(url)
        if info.get("status") != "success":
            return f"Error extracting YouTube video: {info.get('message', 'Unknown error')}"

        header = f"YouTube Video: \"{info['title']}\" by {info['author']} ({info['url']})\n"
        if info.get("has_transcript"):
            return f"{header}\nFull Spoken Transcript:\n{info['content'][:25000]}"
        else:
            return f"{header}\n{info['content']}"

async def summarize_and_build_brief(
    raw_material: str,
    topic: str,
    sources: List[str],
) -> Dict[str, Any]:
    """
    Produce a structured research brief:
    key_facts, key_points, interesting_angles, sources list.
    Uses map-reduce chunking if document exceeds context limits.
    """
    if not raw_material or len(raw_material.strip()) < 50:
        return {
            "key_facts": [f"Topic focus: {topic}"],
            "key_points": [f"Discussion based on foundation model knowledge for: {topic}"],
            "interesting_angles": ["Exploring practical implications and listener takeaways."],
            "sources": ["Model knowledge (no external documents provided)"],
        }

    # Map-Reduce if content is very long (> 12,000 characters)
    max_chunk = 10000
    if len(raw_material) > max_chunk:
        chunks = [raw_material[i : i + max_chunk] for i in range(0, len(raw_material), max_chunk)]
        partial_summaries = []
        for idx, chunk in enumerate(chunks[:4]): # Limit to first 4 chunks
            system_prompt = "You are a research analyst. Extract the top 4 essential factual points from this text excerpt."
            user_prompt = f"Topic: {topic}\n\nExcerpt:\n{chunk}"
            brief_chunk = await generate_structured_json([
                {"role": "system", "content": system_prompt + " Return JSON: {\"points\": [\"...\"]}"},
                {"role": "user", "content": user_prompt},
            ])
            partial_summaries.extend(brief_chunk.get("points", []))
        condensed_material = "\n".join(partial_summaries)
    else:
        condensed_material = raw_material

    system_prompt = (
        "You are an expert podcast research producer. Generate a structured research brief for an upcoming podcast episode.\n"
        "Strict Rule: Ground the facts and points strictly in the provided material. Do not invent citations or false claims.\n"
        "Return valid JSON matching this schema:\n"
        "{\n"
        '  "key_facts": ["fact 1", "fact 2", ...],\n'
        '  "key_points": ["point 1", "point 2", ...],\n'
        '  "interesting_angles": ["angle 1", "angle 2", ...],\n'
        '  "sources": ["source 1", ...]\n'
        "}"
    )

    user_prompt = (
        f"Topic: {topic}\n"
        f"Provided Sources: {', '.join(sources) if sources else 'Direct user input'}\n\n"
        f"Reference Content:\n{condensed_material[:12000]}"
    )

    try:
        brief = await generate_structured_json([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        if not brief.get("sources"):
            brief["sources"] = sources or ["User-provided input material"]
        return brief
    except Exception as e:
        logger.error(f"Failed to generate structured research brief: {e}")
        return {
            "key_facts": [f"Overview of {topic}"],
            "key_points": ["Key conversational discussion points."],
            "interesting_angles": ["Listener perspective & practical insights."],
            "sources": sources or ["User prompt"],
        }

