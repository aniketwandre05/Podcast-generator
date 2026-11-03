import React, { useState } from 'react';
import { X, Sparkles, FileText, Globe, Play, Loader2, Music, Users, Clock } from 'lucide-react';
import type { SpeakerConfig } from '../types';

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

  const [speakers, setSpeakers] = useState<SpeakerConfig[]>([
    { speaker_id: 'HOST', display_name: 'Shubh', voice: 'shubh', pace: 1.0, language_code: 'en-IN' },
    { speaker_id: 'GUEST', display_name: 'Priya', voice: 'priya', pace: 1.0, language_code: 'en-IN' },
    { speaker_id: 'EXPERT', display_name: 'Aditya', voice: 'aditya', pace: 1.0, language_code: 'en-IN' },
  ]);

  if (!isOpen) return null;

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
          source_type: sourceType,
          source_content: sourceContent,
          language,
          dialogue_style: dialogueStyle,
          tone,
          target_duration_mins: durationMins,
          speakers: activeSpeakers,
          background_music: bgMusic,
          music_volume: 0.12,
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
                <FileText className="h-3.5 w-3.5" />
                <span>Doc / Notes</span>
              </button>
            </div>
          </div>

          {/* Topic & Details */}
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

          {/* Extra source content (URL or Document paste) */}
          {sourceType !== 'prompt' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                {sourceType === 'url' ? 'Target Webpage URL' : 'Document Content / Reference Notes'}
              </label>
              {sourceType === 'url' ? (
                <input
                  type="url"
                  value={sourceContent}
                  onChange={(e) => setSourceContent(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
                />
              ) : (
                <textarea
                  rows={3}
                  value={sourceContent}
                  onChange={(e) => setSourceContent(e.target.value)}
                  placeholder="Paste article, study notes, or transcript excerpts here..."
                  className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm"
                />
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
