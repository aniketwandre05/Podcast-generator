# Sarvam AI API Verification & Architecture Notes

This document provides verified specifications for the **Sarvam AI APIs** used across the **PodcastAI** application, compiled from official documentation (https://docs.sarvam.ai) and the official `sarvamai` SDK (v0.1.42).

---

## 1. Authentication & Base URL

* **Base URL**: `https://api.sarvam.ai`
* **Authentication Header**: `api-subscription-key: <SARVAM_API_KEY>`
* **Environment Variable**: `SARVAM_API_KEY` (loaded from `.env`, never exposed to browser or committed to git).

---

## 2. Text-to-Speech (Bulbul)

### Endpoint
* **Path**: `POST https://api.sarvam.ai/text-to-speech`

### Supported Models & Character Limits
1. **`bulbul:v3`** (Recommended for stability & quality)
   * **Character Limit**: 2,500 characters per request.
   * **Default Voice**: `shubh`
   * **Pace Range**: `0.5` to `2.0` (default `1.0`)
   * **Temperature**: `0.01` to `1.0` (default `0.6` for natural expressiveness)
   * **Pitch / Loudness**: Not supported on v3.
   * **Preprocessing**: Automatically enabled.
2. **`bulbul:v4-flash`** (Latest high-speed model with 200+ persona voices)
   * **Character Limit**: 2,500 characters per request.
   * **Default Voice**: `shubh_enhi_ads`
   * **Pace Range**: `0.5` to `2.0`
3. **`bulbul:v2`** (Legacy)
   * **Character Limit**: 1,500 characters.
   * **Supports Pitch**: `-0.75` to `0.75` (default `0.0`)
   * **Supports Loudness**: `0.3` to `3.0` (default `1.0`)

### Supported Language Codes (BCP-47)
* `en-IN`: English (India)
* `hi-IN`: Hindi
* `bn-IN`: Bengali
* `ta-IN`: Tamil
* `te-IN`: Telugu
* `kn-IN`: Kannada
* `ml-IN`: Malayalam
* `mr-IN`: Marathi
* `gu-IN`: Gujarati
* `pa-IN`: Punjabi
* `od-IN`: Odia

### Voice Catalog (`bulbul:v3`)
* **Male**: `shubh` (default), `aditya`, `rahul`, `rohan`, `amit`, `dev`, `ratan`, `varun`, `manan`, `sumit`, `kabir`, `aayan`, `ashutosh`, `advait`, `anand`, `tarun`, `sunny`, `mani`, `gokul`, `vijay`, `mohit`, `rehan`, `soham`.
* **Female**: `ritu`, `priya`, `neha`, `pooja`, `simran`, `kavya`, `ishita`, `shreya`, `roopa`, `tanya`, `shruti`, `suhani`, `kavitha`, `rupali`.

### Audio Formats & Sample Rates
* **Codecs**: `wav`, `mp3`, `aac`, `flac`, `linear16`.
* **Sample Rates**: `8000`, `16000`, `22050` (default), `24000`, `32000`, `44100`, `48000` Hz.

### Response Format
```json
{
  "request_id": "20261103_d7061a9f-257d-45c5-97e9-b643d6e9134f",
  "audios": [
    "UklGRiS6AQBXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ..."
  ]
}
```
* The output is a base64-encoded WAV/MP3 string in `audios[0]`.

---

## 3. Chat Completions & LLM

### Endpoint
* **Path**: `POST https://api.sarvam.ai/v1/chat/completions` (OpenAI compatible)

### Supported Models
* **`sarvam-105b-conversations`**: Specially optimized for conversational scripts, natural dialogue, turn-taking, and voice agents across English and Indian languages. Context window: 32K tokens.
* **`sarvam-105b`**: Flagship foundation model with 128K context window for heavy research, summarization, and map-reduce tasks.
* **`sarvam-m`**: Multilingual foundation model.

### Request Parameters
* `messages`: `[{"role": "system"|"user"|"assistant", "content": "..."}]`
* `model`: Model identifier.
* `temperature`: `0.0` to `2.0` (typically `0.6` to `0.8`).
* `max_tokens`: Maximum tokens to generate.
* `response_format`: `{"type": "json_object"}` (optional JSON enforcement).

### Response Format
```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 450,
    "total_tokens": 570
  }
}
```

---

## 4. Text Translation API

### Endpoint
* **Path**: `POST https://api.sarvam.ai/translate`

### Supported Models
* **`mayura:v1`**: High-quality colloquial and formal translation across 12 languages. Supports automatic language detection (`auto`), modes (`formal`, `classic-colloquial`, `modern-colloquial`, `code-mixed`), and roman transliteration. Max 1,000 characters per request.
* **`sarvam-translate:v1`**: Supports all 22 scheduled Indian languages. Max 2,000 characters per request.

### Parameters
* `input`: Text to translate.
* `source_language_code`: e.g. `en-IN`, `hi-IN`, or `auto`.
* `target_language_code`: e.g. `hi-IN`, `ta-IN`, etc.
* `mode`: `formal` | `classic-colloquial` | `modern-colloquial` | `code-mixed`.
* `model`: `mayura:v1` | `sarvam-translate:v1`.

### Response Format
```json
{
  "translated_text": "..."
}
```

---

## 5. Architectural Implications for PodcastAI

1. **Turn Chunking**:
   Any dialogue turn exceeding ~2,000 characters will be segmented along sentence boundaries (`. `, `? `, `! `, `। `) before calling Bulbul, then stitched seamlessly in audio space.
2. **Concurrency & Rate Limiting**:
   TTS calls are executed via an async semaphore (concurrency = 4) with exponential backoff and jitter for `429 Too Many Requests` or `5xx Server Errors`.
3. **Caching**:
   TTS outputs are cached in SQLite by an MD5/SHA256 hash of `(text, speaker, language_code, pace, model)`. When a user edits only 1 line in the script editor, only that single turn is synthesized again.
4. **Dialogue Style**:
   The LLM prompt uses structured system prompts enforcing realistic conversational dynamics: brief affirmations, interruptions, questions, natural cadence, and strict JSON output parsing.

