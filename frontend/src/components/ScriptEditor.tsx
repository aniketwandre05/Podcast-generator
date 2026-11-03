import React, { useState } from 'react';
import { ArrowLeft, Save, Languages, Plus, Trash2, Clock, Volume2, Loader2 } from 'lucide-react';
import type { Episode, Script, Turn } from '../types';

interface ScriptEditorProps {
  episode: Episode;
  onBack: () => void;
  onUpdated: () => void;
}

const LANGUAGES = [
  { code: 'hi-IN', name: 'Hindi (हिंदी)' },
  { code: 'bn-IN', name: 'Bengali (বাংলা)' },
  { code: 'ta-IN', name: 'Tamil (தமிழ்)' },
  { code: 'te-IN', name: 'Telugu (తెలుగు)' },
  { code: 'kn-IN', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml-IN', name: 'Malayalam (മലയാളം)' },
  { code: 'mr-IN', name: 'Marathi (मराठी)' },
  { code: 'gu-IN', name: 'Gujarati (ગુજરાતી)' },
  { code: 'pa-IN', name: 'Punjabi (ਪੰਜਾਬੀ)' },
  { code: 'od-IN', name: 'Odia (ଓଡ଼ିଆ)' },
  { code: 'en-IN', name: 'English (India)' },
];

export const ScriptEditor: React.FC<ScriptEditorProps> = ({ episode, onBack, onUpdated }) => {
  const [script, setScript] = useState<Script>(
    episode.script || { title: episode.title, description: episode.description, segments: [] }
  );
  const [isSaving, setIsSaving] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [translateOpen, setTranslateOpen] = useState(false);
  const [targetLang, setTargetLang] = useState('hi-IN');
  const [isTranslating, setIsTranslating] = useState(false);

  const speakerIds = episode.speakers_config?.map((s) => s.speaker_id) || ['HOST', 'GUEST'];

  const handleTurnChange = (segIdx: number, turnIdx: number, field: keyof Turn, val: any) => {
    const updated = { ...script };
    updated.segments[segIdx].turns[turnIdx] = {
      ...updated.segments[segIdx].turns[turnIdx],
      [field]: val,
    };
    setScript(updated);
  };

  const handleAddTurn = (segIdx: number) => {
    const updated = { ...script };
    updated.segments[segIdx].turns.push({
      speaker: speakerIds[0],
      text: 'New line of dialogue...',
      emotion: 'natural',
      pause_after_ms: 350,
    });
    setScript(updated);
  };

  const handleDeleteTurn = (segIdx: number, turnIdx: number) => {
    const updated = { ...script };
    updated.segments[segIdx].turns.splice(turnIdx, 1);
    setScript(updated);
  };

  const handleSaveScript = async () => {
    setIsSaving(true);
    try {
      await fetch(`/api/episodes/${episode.id}/script`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script }),
      });
      alert('Script saved successfully!');
    } catch (e) {
      console.error(e);
      alert('Failed to save script');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAndSynthesize = async () => {
    setIsSynthesizing(true);
    try {
      // 1. Save
      await fetch(`/api/episodes/${episode.id}/script`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script }),
      });
      // 2. Synthesize
      await fetch(`/api/episodes/${episode.id}/synthesize`, {
        method: 'POST',
      });
      onUpdated();
    } catch (e) {
      console.error(e);
      alert('Failed to trigger audio synthesis');
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleTranslate = async () => {
    setIsTranslating(true);
    try {
      const res = await fetch(`/api/episodes/${episode.id}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_language_code: targetLang, mode: 'modern-colloquial' }),
      });
      if (res.ok) {
        setTranslateOpen(false);
        onUpdated();
      }
    } catch (e) {
      console.error(e);
      alert('Translation failed');
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto my-8 px-4">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <button
          onClick={onBack}
          className="flex items-center space-x-1.5 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Player</span>
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setTranslateOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            <Languages className="h-4 w-4 text-purple-400" />
            <span>Translate Episode</span>
          </button>

          <button
            onClick={handleSaveScript}
            disabled={isSaving}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4 text-emerald-400" />}
            <span>Save Draft</span>
          </button>

          <button
            onClick={handleSaveAndSynthesize}
            disabled={isSynthesizing}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-md shadow-indigo-500/20"
          >
            {isSynthesizing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
            <span>Save & Re-Synthesize Audio</span>
          </button>
        </div>
      </div>

      {/* Episode Title & Description Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
          Episode Title
        </label>
        <input
          type="text"
          value={script.title}
          onChange={(e) => setScript({ ...script, title: e.target.value })}
          className="w-full text-xl font-bold bg-transparent border-b border-slate-800 text-white pb-2 focus:outline-none focus:border-indigo-500 mb-4"
        />

        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
          Show Notes Synopsis
        </label>
        <textarea
          rows={2}
          value={script.description}
          onChange={(e) => setScript({ ...script, description: e.target.value })}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      {/* Segments & Turns List */}
      <div className="space-y-6">
        {script.segments.map((seg, segIdx) => (
          <div key={segIdx} className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
            <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xs px-2 py-0.5 rounded-md font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Part {segIdx + 1}
                </span>
                <input
                  type="text"
                  value={seg.name}
                  onChange={(e) => {
                    const up = { ...script };
                    up.segments[segIdx].name = e.target.value;
                    setScript(up);
                  }}
                  className="font-bold text-white bg-transparent border-none text-sm focus:outline-none"
                />
              </div>
              <span className="text-xs text-slate-500">{seg.turns.length} Turns</span>
            </div>

            <div className="p-4 space-y-4">
              {seg.turns.map((turn, turnIdx) => (
                <div
                  key={turnIdx}
                  className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-xl hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center space-x-2">
                      <select
                        value={turn.speaker}
                        onChange={(e) => handleTurnChange(segIdx, turnIdx, 'speaker', e.target.value)}
                        className="px-2.5 py-1 bg-indigo-950/50 border border-indigo-500/30 text-indigo-300 font-bold rounded-lg text-xs"
                      >
                        {speakerIds.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>

                      <input
                        type="text"
                        value={turn.emotion || ''}
                        onChange={(e) => handleTurnChange(segIdx, turnIdx, 'emotion', e.target.value)}
                        placeholder="Emotion tag"
                        className="w-24 px-2 py-0.5 bg-slate-900 border border-slate-800 rounded-md text-[11px] text-slate-400"
                      />
                    </div>

                    <div className="flex items-center space-x-3 text-xs">
                      <div className="flex items-center space-x-1 text-slate-400">
                        <Clock className="h-3 w-3" />
                        <input
                          type="number"
                          step={50}
                          value={turn.pause_after_ms}
                          onChange={(e) =>
                            handleTurnChange(segIdx, turnIdx, 'pause_after_ms', Number(e.target.value))
                          }
                          className="w-14 px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-center text-slate-200"
                        />
                        <span>ms gap</span>
                      </div>

                      <button
                        onClick={() => handleDeleteTurn(segIdx, turnIdx)}
                        className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900 transition-colors"
                        title="Delete Turn"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <textarea
                    rows={2}
                    value={turn.text}
                    onChange={(e) => handleTurnChange(segIdx, turnIdx, 'text', e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs sm:text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              ))}

              <button
                type="button"
                onClick={() => handleAddTurn(segIdx)}
                className="w-full py-2 border border-dashed border-slate-800 hover:border-slate-700 rounded-xl text-xs font-semibold text-slate-400 hover:text-white flex items-center justify-center space-x-1 transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add Dialogue Line</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Translate Modal */}
      {translateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center space-x-2">
              <Languages className="h-5 w-5 text-purple-400" />
              <span>Translate Episode with Sarvam</span>
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Localize the entire episode dialogue into another Indian language using Sarvam Mayura Translate, then automatically re-synthesize audio.
            </p>

            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Target Language
            </label>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm mb-6"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>

            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setTranslateOpen(false)}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleTranslate}
                disabled={isTranslating}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white flex items-center space-x-2"
              >
                {isTranslating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Translating & Synthesizing...</span>
                  </>
                ) : (
                  <span>Start Translation</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
