import React, { useState } from 'react';
import {
  X,
  Sparkles,
  FileText,
  Globe,
  Play,
  Loader2,
  Music,
  Users,
  Clock,
  UploadCloud,
  FileCheck,
  Trash2,
  AlertCircle,
  Eye,
  EyeOff,
  Video,
  Link2,
  Plus,
  FilePlus,
  Layers,
} from 'lucide-react';
import type { SpeakerConfig, SourceItem } from '../types';

interface CreateEpisodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (episodeId: string) => void;
}

const TONES = [
  { id: 'casual', label: 'Casual & Banter', desc: 'Relaxed, conversational back-and-forth' },
  { id: 'educational', label: 'Educational & Deep-Dive', desc: 'Informative, structured exploration' },
  { id: 'debate', label: 'Friendly Debate', desc: 'Contrasting viewpoints & lively discussion' },
  { id: 'interview', label: 'Interview Spotlight', desc: 'Host interviewing a domain expert' },
  { id: 'storytelling', label: 'Narrative Storytelling', desc: 'Cinematic, engaging storytelling' },
  { id: 'news-brief', label: 'News Digest', desc: 'Crisp, fast-paced headline briefing' },
];

const LANGUAGES = [
  { code: 'en-IN', name: 'English (India)' },
  { code: 'hi-IN', name: 'Hindi (हिंदी / Hinglish)' },
  { code: 'bn-IN', name: 'Bengali (বাংলা)' },
  { code: 'ta-IN', name: 'Tamil (தமிழ்)' },
  { code: 'te-IN', name: 'Telugu (తెలుగు)' },
  { code: 'kn-IN', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml-IN', name: 'Malayalam (മലയാളം)' },
  { code: 'mr-IN', name: 'Marathi (मराठी)' },
  { code: 'gu-IN', name: 'Gujarati (ગુજરાતી)' },
  { code: 'pa-IN', name: 'Punjabi (ਪੰਜਾਬੀ)' },
  { code: 'od-IN', name: 'Odia (ଓଡ଼ିଆ)' },
];

const DIALOGUE_STYLES = [
  { id: 'code_mixed', label: 'Conversational Code-Mixed', desc: 'Natural blend of Indic language & English (Hinglish/Tanglish)' },
  { id: 'native', label: 'Pure Native Script', desc: 'Authentic regional phrasing in native Indic script' },
  { id: 'english_indian', label: 'Indian English', desc: 'Contemporary Indian English with regional nuance' },
  { id: 'bilingual', label: 'Bilingual / Cross-Lingual', desc: 'Speakers converse across different languages' },
];

const PRESET_VOICES = [
  { id: 'shubh', name: 'Shubh (Male, Authoritative)' },
  { id: 'priya', name: 'Priya (Female, Energetic)' },
  { id: 'rohan', name: 'Rohan (Male, Casual)' },
  { id: 'simran', name: 'Simran (Female, Relatable)' },
  { id: 'aditya', name: 'Aditya (Male, Intellectual)' },
  { id: 'kavya', name: 'Kavya (Female, Insightful)' },
  { id: 'kabir', name: 'Kabir (Male, Deep Narrator)' },
  { id: 'ritu', name: 'Ritu (Female, Calm Storyteller)' },
];

export const CreateEpisodeModal: React.FC<CreateEpisodeModalProps> = ({ isOpen, onClose, onCreated }) => {
  const [sourceType, setSourceType] = useState<'prompt' | 'url' | 'document'>('prompt');
  const [topic, setTopic] = useState('');
  const [sourceContent, setSourceContent] = useState('');
  const [language, setLanguage] = useState('en-IN');
  const [dialogueStyle, setDialogueStyle] = useState('code_mixed');
  const [tone, setTone] = useState('casual');
  const [durationMins, setDurationMins] = useState(5);
  const [bgMusic, setBgMusic] = useState('chill_ambient.wav');
  const [numSpeakers, setNumSpeakers] = useState(2);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewPlaying, setPreviewPlaying] = useState<string | null>(null);

  // Multi-source state (NotebookLM style: multi-file, YouTube, Web links, notes)
  const [sourcesList, setSourcesList] = useState<SourceItem[]>([]);
  const [activeSourceTab, setActiveSourceTab] = useState<'files' | 'link' | 'note'>('files');
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [docUploadError, setDocUploadError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Link input state (YouTube / Web)
  const [linkInput, setLinkInput] = useState('');
  const [isAddingLink, setIsAddingLink] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);

  // Quick note state
  const [noteTitle, setNoteTitle] = useState('');
  const [noteContent, setNoteContent] = useState('');

  // Preview source modal/accordion
  const [previewingSourceId, setPreviewingSourceId] = useState<string | null>(null);

  const [speakers, setSpeakers] = useState<SpeakerConfig[]>([
    { speaker_id: 'HOST', display_name: 'Shubh', voice: 'shubh', pace: 1.0, language_code: 'en-IN' },
    { speaker_id: 'GUEST', display_name: 'Priya', voice: 'priya', pace: 1.0, language_code: 'en-IN' },
    { speaker_id: 'EXPERT', display_name: 'Aditya', voice: 'aditya', pace: 1.0, language_code: 'en-IN' },
  ]);

  if (!isOpen) return null;

  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleUploadFiles = async (fileList: FileList | File[]) => {
    setDocUploadError(null);
    const validFiles: File[] = [];
    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];

    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i];
      const name = f.name.toLowerCase();
      if (validExtensions.some((ext) => name.endsWith(ext))) {
        validFiles.push(f);
      }
    }

    if (validFiles.length === 0) {
      setDocUploadError('Unsupported format. Please upload PDF, Word (.docx), Markdown (.md), or Text (.txt) files.');
      return;
    }

    setIsUploadingDoc(true);
    try {
      const formData = new FormData();
      validFiles.forEach((f) => formData.append('files', f));

      const res = await fetch('/api/episodes/upload-docs', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error('Failed to upload and extract documents.');
      }

      const data = await res.json();
      if (data.sources && data.sources.length > 0) {
        const newItems: SourceItem[] = data.sources.map((s: any) => ({
          id: s.id,
          source_type: 'file',
          title: s.title,
          content: s.content, // file path for generator
          file_type: s.file_type,
          file_size: s.file_size,
          word_count: s.word_count,
        }));

        setSourcesList((prev) => [...prev, ...newItems]);

        if (!topic.trim() && newItems.length > 0) {
          setTopic(newItems[0].title);
        }
      }
    } catch (err: any) {
      console.error(err);
      setDocUploadError(err.message || 'Error processing documents.');
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUploadFiles(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleAddLink = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!linkInput.trim()) return;

    setLinkError(null);
    setIsAddingLink(true);

    try {
      const res = await fetch('/api/episodes/extract-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: linkInput.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not extract content from URL');
      }

      const data = await res.json();
      const newItem: SourceItem = {
        id: Math.random().toString(36).substring(7),
        source_type: data.source_type, // 'youtube' or 'url'
        title: data.title || (data.source_type === 'youtube' ? 'YouTube Video' : 'Web Article'),
        content: data.content,
        url: data.url,
        author: data.author,
        word_count: data.word_count || 0,
        has_transcript: data.has_transcript || false,
      };

      setSourcesList((prev) => [...prev, newItem]);
      setLinkInput('');

      if (!topic.trim() && newItem.title) {
        setTopic(newItem.title);
      }
    } catch (err: any) {
      console.error(err);
      setLinkError(err.message || 'Failed to extract content from link.');
    } finally {
      setIsAddingLink(false);
    }
  };

  const handleAddNote = () => {
    if (!noteContent.trim()) return;
    const title = noteTitle.trim() || `Notes ${sourcesList.length + 1}`;
    const words = noteContent.trim().split(/\s+/).filter(Boolean).length;
    const newItem: SourceItem = {
      id: Math.random().toString(36).substring(7),
      source_type: 'text',
      title,
      content: noteContent.trim(),
      word_count: words,
    };
    setSourcesList((prev) => [...prev, newItem]);
    setNoteTitle('');
    setNoteContent('');

    if (!topic.trim()) {
      setTopic(title);
    }
  };

  const handleRemoveSource = (id?: string) => {
    setSourcesList((prev) => prev.filter((s) => s.id !== id));
  };

  const handleSpeakerChange = (index: number, field: keyof SpeakerConfig, value: any) => {
    const updated = [...speakers];
    updated[index] = { ...updated[index], [field]: value };
    setSpeakers(updated);
  };

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    setSpeakers(speakers.map(s => ({
      ...s,
      language_code: newLang,
    })));
  };

  const handlePreviewVoice = async (voiceId: string, langCode?: string) => {
    try {
      setPreviewPlaying(voiceId);
      const res = await fetch('/api/voices/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice: voiceId, language_code: langCode || language }),
      });
      const data = await res.json();
      if (data.audio_base64) {
        const audio = new Audio(data.audio_base64);
        audio.onended = () => setPreviewPlaying(null);
        await audio.play();
      } else {
        setPreviewPlaying(null);
      }
    } catch (e) {
      console.error(e);
      setPreviewPlaying(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsSubmitting(true);
    try {
      const activeSpeakers = speakers.slice(0, numSpeakers).map(s => ({
        ...s,
        language_code: s.language_code || language,
      }));

      const res = await fetch('/api/episodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          source_type: sourcesList.length > 0 ? 'multi_source' : sourceType,
          source_content: sourceContent,
          language,
          dialogue_style: dialogueStyle,
          tone,
          target_duration_mins: durationMins,
          speakers: activeSpeakers,
          background_music: bgMusic,
          music_volume: 0.12,
          sources: sourcesList.length > 0 ? sourcesList : undefined,
        }),
      });

      const data = await res.json();
      if (data.id) {
        onCreated(data.id);
        onClose();
      }
    } catch (err) {
      console.error('Failed to create episode', err);
      alert('Error creating episode. Check console for details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 my-8 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center space-x-2 mb-1">
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <h2 className="text-xl font-bold text-white">Create New Episode</h2>
        </div>
        <p className="text-sm text-slate-400 mb-6">
          Generate an end-to-end multi-speaker podcast with Sarvam AI.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Source Type Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Source Material
            </label>
            <div className="grid grid-cols-3 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setSourceType('prompt')}
                className={`py-2 px-3 rounded-lg text-xs font-medium flex items-center justify-center space-x-1.5 transition-all ${
                  sourceType === 'prompt' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Topic Prompt</span>
              </button>
              <button
                type="button"
                onClick={() => setSourceType('url')}
                className={`py-2 px-3 rounded-lg text-xs font-medium flex items-center justify-center space-x-1.5 transition-all ${
                  sourceType === 'url' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Globe className="h-3.5 w-3.5" />
                <span>Web URL</span>
              </button>
              <button
                type="button"
                onClick={() => setSourceType('document')}
                className={`py-2 px-3 rounded-lg text-xs font-medium flex items-center justify-center space-x-1.5 transition-all ${
                  sourceType === 'document' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="h-3.5 w-3.5 text-indigo-300" />
                <span>Research Studio</span>
              </button>
            </div>
          </div>

          {/* Episode Topic / Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Episode Topic / Title
            </label>
            <input
              type="text"
              required
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Breakthroughs in Quantum Computing & Indian Deep Tech"
              className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          {/* Single Web URL mode */}
          {sourceType === 'url' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Target Webpage URL
              </label>
              <input
                type="url"
                value={sourceContent}
                onChange={(e) => setSourceContent(e.target.value)}
                placeholder="https://example.com/article"
                className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}

          {/* Multi-Source NotebookLM-style Research Studio */}
          {sourceType === 'document' && (
            <div className="space-y-4 p-4 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              {/* Studio Header & Sub-Tabs */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                    NotebookLM Multi-Source Studio
                  </span>
                </div>
                <div className="flex items-center space-x-1 p-0.5 bg-slate-900 rounded-lg border border-slate-800 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setActiveSourceTab('files')}
                    className={`px-2.5 py-1 rounded-md flex items-center space-x-1 transition-colors ${
                      activeSourceTab === 'files'
                        ? 'bg-indigo-600 text-white font-medium shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <FilePlus className="h-3 w-3" />
                    <span>Drop Files</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveSourceTab('link')}
                    className={`px-2.5 py-1 rounded-md flex items-center space-x-1 transition-colors ${
                      activeSourceTab === 'link'
                        ? 'bg-indigo-600 text-white font-medium shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Video className="h-3 w-3" />
                    <span>YouTube / Web</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveSourceTab('note')}
                    className={`px-2.5 py-1 rounded-md flex items-center space-x-1 transition-colors ${
                      activeSourceTab === 'note'
                        ? 'bg-indigo-600 text-white font-medium shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <FileText className="h-3 w-3" />
                    <span>Notes</span>
                  </button>
                </div>
              </div>

              {/* Sub-Tab 1: Multi-File Drag & Drop */}
              {activeSourceTab === 'files' && (
                <div>
                  <div
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={() => document.getElementById('multi-file-input')?.click()}
                    className={`relative border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                      isDragOver
                        ? 'border-indigo-500 bg-indigo-500/10 ring-4 ring-indigo-500/20'
                        : 'border-slate-800 hover:border-indigo-500/60 bg-slate-900/60 hover:bg-slate-900'
                    }`}
                  >
                    <input
                      id="multi-file-input"
                      type="file"
                      multiple
                      accept=".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          handleUploadFiles(e.target.files);
                        }
                      }}
                    />

                    {isUploadingDoc ? (
                      <div className="py-3 flex flex-col items-center justify-center space-y-2">
                        <Loader2 className="h-8 w-8 text-indigo-400 animate-spin" />
                        <p className="text-sm font-medium text-slate-200">Parsing and extracting documents...</p>
                        <p className="text-xs text-slate-400">Extracting chapters, word counts, and key themes</p>
                      </div>
                    ) : (
                      <div className="py-2 flex flex-col items-center justify-center space-y-2">
                        <div className="p-3 bg-indigo-500/10 rounded-2xl text-indigo-400 border border-indigo-500/20">
                          <UploadCloud className="h-7 w-7" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-200">
                            <span className="text-indigo-400">Click to upload</span> or drag and drop files
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            Upload multiple PDF, Word (.docx), Markdown (.md), or Text (.txt) files simultaneously
                          </p>
                        </div>
                        <div className="flex items-center space-x-1.5 pt-1">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                            PDF
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-bold">
                            DOCX
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold">
                            TXT
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 font-bold">
                            MD
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {docUploadError && (
                    <div className="mt-2 p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-xs text-rose-300">
                      <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                      <span>{docUploadError}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-Tab 2: YouTube / Web Link Ingestion */}
              {activeSourceTab === 'link' && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <div className="relative flex-1">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <Link2 className="h-4 w-4" />
                      </div>
                      <input
                        type="url"
                        value={linkInput}
                        onChange={(e) => setLinkInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddLink();
                          }
                        }}
                        placeholder="https://youtube.com/watch?v=... or https://example.com/article"
                        className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-500"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => handleAddLink()}
                      disabled={isAddingLink || !linkInput.trim()}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition-colors shrink-0"
                    >
                      {isAddingLink ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Extracting...</span>
                        </>
                      ) : (
                        <>
                          <Plus className="h-3.5 w-3.5" />
                          <span>Extract & Add</span>
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    💡 Paste any YouTube video URL to automatically fetch spoken transcripts, titles, and channel metadata, or paste any blog/news article.
                  </p>

                  {linkError && (
                    <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-2 text-xs text-rose-300">
                      <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                      <span>{linkError}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-Tab 3: Custom Notes */}
              {activeSourceTab === 'note' && (
                <div className="space-y-2.5">
                  <input
                    type="text"
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    placeholder="Note title (e.g. Host Talking Points / Meeting Notes)"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <textarea
                    rows={3}
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    placeholder="Write or paste your custom research, outline ideas, or interview questions..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500"
                  />
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={handleAddNote}
                      disabled={!noteContent.trim()}
                      className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded-xl flex items-center space-x-1.5 transition-colors"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      <span>Add Note to Sources</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Ingested Sources Deck */}
              {sourcesList.length > 0 ? (
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold text-white">Ingested Sources</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                        {sourcesList.length} items
                      </span>
                      <span className="text-[11px] text-slate-400">
                        ({sourcesList.reduce((acc, s) => acc + (s.word_count || 0), 0).toLocaleString()} words total)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSourcesList([])}
                      className="text-[11px] text-slate-400 hover:text-rose-400 transition-colors"
                    >
                      Clear All
                    </button>
                  </div>

                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {sourcesList.map((s) => (
                      <div
                        key={s.id}
                        className="p-2.5 bg-slate-900/90 border border-slate-800/90 rounded-xl flex flex-col space-y-1.5 transition-all hover:border-slate-700"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2.5 min-w-0">
                            {/* Type Icon Badge */}
                            {s.source_type === 'youtube' && (
                              <div className="p-1.5 bg-rose-500/10 text-rose-400 rounded-lg border border-rose-500/20 shrink-0">
                                <Video className="h-3.5 w-3.5" />
                              </div>
                            )}
                            {s.source_type === 'file' && (
                              <div className="p-1.5 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20 shrink-0">
                                <FileCheck className="h-3.5 w-3.5" />
                              </div>
                            )}
                            {s.source_type === 'url' && (
                              <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20 shrink-0">
                                <Globe className="h-3.5 w-3.5" />
                              </div>
                            )}
                            {s.source_type === 'text' && (
                              <div className="p-1.5 bg-purple-500/10 text-purple-400 rounded-lg border border-purple-500/20 shrink-0">
                                <FileText className="h-3.5 w-3.5" />
                              </div>
                            )}

                            {/* Title & Metadata */}
                            <div className="min-w-0">
                              <p className="text-xs font-semibold text-slate-100 truncate max-w-[280px] sm:max-w-sm">
                                {s.title}
                              </p>
                              <div className="text-[10px] text-slate-400 flex items-center space-x-1.5">
                                {s.source_type === 'youtube' && (
                                  <span className="text-rose-400 font-medium">YouTube Transcript</span>
                                )}
                                {s.source_type === 'file' && (
                                  <span className="uppercase text-blue-400 font-medium">{s.file_type}</span>
                                )}
                                {s.source_type === 'url' && (
                                  <span className="text-emerald-400 font-medium">Web Article</span>
                                )}
                                {s.source_type === 'text' && (
                                  <span className="text-purple-400 font-medium">Custom Note</span>
                                )}
                                <span>•</span>
                                <span>{(s.word_count || 0).toLocaleString()} words</span>
                                {s.file_size ? (
                                  <>
                                    <span>•</span>
                                    <span>{formatBytes(s.file_size)}</span>
                                  </>
                                ) : null}
                                {s.author && (
                                  <>
                                    <span>•</span>
                                    <span className="truncate max-w-[120px]">{s.author}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex items-center space-x-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => setPreviewingSourceId(previewingSourceId === s.id ? null : (s.id || null))}
                              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
                              title={previewingSourceId === s.id ? 'Hide Content' : 'Preview Content'}
                            >
                              {previewingSourceId === s.id ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoveSource(s.id)}
                              className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-rose-500/10 transition-colors"
                              title="Remove Source"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Expandable Preview */}
                        {previewingSourceId === s.id && (
                          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-slate-300 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                            {s.content ? (
                              s.content.length > 500 ? `${s.content.slice(0, 500)}...` : s.content
                            ) : (
                              <span className="italic text-slate-500">File uploaded and stored for server-side synthesis.</span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="py-2 px-3 bg-slate-900/40 border border-dashed border-slate-800/80 rounded-xl text-center">
                  <p className="text-[11px] text-slate-400">
                    Add files, YouTube videos, or notes above to build your multi-source research dossier.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Episode Settings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Primary Episode Language
              </label>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Episode Tone
              </label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
              >
                {TONES.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center space-x-1">
                <Clock className="h-3.5 w-3.5 text-indigo-400" />
                <span>Target Duration</span>
              </label>
              <select
                value={durationMins}
                onChange={(e) => setDurationMins(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
              >
                <option value={5}>5 Minutes (~750 words)</option>
                <option value={10}>10 Minutes (~1,500 words)</option>
                <option value={15}>15 Minutes (~2,250 words)</option>
                <option value={20}>20 Minutes (~3,000 words)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center space-x-1">
                <Music className="h-3.5 w-3.5 text-indigo-400" />
                <span>Background Music</span>
              </label>
              <select
                value={bgMusic}
                onChange={(e) => setBgMusic(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
              >
                <option value="chill_ambient.wav">Chill Ambient Bed</option>
                <option value="upbeat_intro.wav">Upbeat Rhythmic</option>
                <option value="corporate_outro.wav">Corporate Synth</option>
                <option value="none">No Background Music</option>
              </select>
            </div>
          </div>

          {/* Multilingual Dialogue Style */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Multilingual Dialogue Style
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {DIALOGUE_STYLES.map((style) => (
                <button
                  key={style.id}
                  type="button"
                  onClick={() => setDialogueStyle(style.id)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    dialogueStyle === style.id
                      ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500/50'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-200">{style.label}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{style.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Speakers Configuration */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1">
                <Users className="h-3.5 w-3.5 text-indigo-400" />
                <span>Cast & Voices (Bulbul:v3 Multilingual)</span>
              </label>
              <div className="flex items-center space-x-1 text-xs">
                {[1, 2, 3].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setNumSpeakers(num)}
                    className={`px-2.5 py-1 rounded-md transition-colors ${
                      numSpeakers === num ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {num} {num === 1 ? 'Speaker' : 'Speakers'}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {speakers.slice(0, numSpeakers).map((sp, idx) => (
                <div key={sp.speaker_id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex flex-wrap sm:flex-nowrap items-center gap-2">
                  <div className="w-14">
                    <span className="text-[11px] font-bold text-indigo-400 uppercase">{sp.speaker_id}</span>
                  </div>
                  <input
                    type="text"
                    value={sp.display_name}
                    onChange={(e) => handleSpeakerChange(idx, 'display_name', e.target.value)}
                    placeholder="Name"
                    className="w-24 px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  />
                  <select
                    value={sp.voice}
                    onChange={(e) => handleSpeakerChange(idx, 'voice', e.target.value)}
                    className="flex-1 min-w-[120px] px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white"
                  >
                    {PRESET_VOICES.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </select>
                  <select
                    value={sp.language_code || language}
                    onChange={(e) => handleSpeakerChange(idx, 'language_code', e.target.value)}
                    className="w-28 px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200"
                    title="Speaker Language"
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.name.split(' ')[0]} ({l.code.split('-')[0]})
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => handlePreviewVoice(sp.voice, sp.language_code || language)}
                    disabled={previewPlaying === sp.voice}
                    className="p-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 transition-colors"
                    title="Preview Voice in Speaker Language"
                  >
                    {previewPlaying === sp.voice ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 fill-current" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-400 hover:text-white font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !topic.trim()}
              className="px-6 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25 disabled:opacity-50 flex items-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Launching Pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Generate Podcast</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
