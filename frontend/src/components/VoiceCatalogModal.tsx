import React, { useEffect, useState } from 'react';
import { Volume2, Play, Loader2 } from 'lucide-react';
import type { Voice } from '../types';

export const VoiceCatalogModal: React.FC = () => {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGender, setSelectedGender] = useState<string>('all');
  const [previewPlaying, setPreviewPlaying] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/voices')
      .then((res) => res.json())
      .then((data) => {
        setVoices(data.voices || []);
        setLoading(false);
      })
      .catch((e) => {
        console.error('Failed to load voices', e);
        setLoading(false);
      });
  }, []);

  const handlePreview = async (voiceId: string) => {
    try {
      setPreviewPlaying(voiceId);
      const res = await fetch('/api/voices/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice: voiceId }),
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

  const filtered = voices.filter(
    (v) => selectedGender === 'all' || v.gender.toLowerCase() === selectedGender.toLowerCase()
  );

  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Volume2 className="h-6 w-6 text-indigo-400" />
            <span>Sarvam Bulbul Voice Catalog</span>
          </h2>
          <p className="text-xs text-slate-400">
            Preview all 30+ native Indian voice personas supported by Bulbul:v3 & v4-flash
          </p>
        </div>

        {/* Gender Filter */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
          {['all', 'male', 'female'].map((g) => (
            <button
              key={g}
              onClick={() => setSelectedGender(g)}
              className={`px-3 py-1.5 rounded-lg capitalize font-medium transition-colors ${
                selectedGender === g ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-indigo-500 mb-2" />
          <p className="text-xs">Loading voice profiles from Sarvam API...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((voice) => (
            <div
              key={voice.id}
              className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between hover:border-slate-700 transition-colors shadow-sm"
            >
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-bold text-white text-sm">{voice.name}</span>
                  <span className="text-[10px] px-2 py-0.2 rounded-full uppercase font-bold bg-slate-800 text-indigo-300">
                    {voice.gender}
                  </span>
                </div>
                <p className="text-xs text-slate-400 max-w-[200px] truncate">{voice.description}</p>
                <span className="text-[10px] text-slate-500">{voice.model}</span>
              </div>

              <button
                onClick={() => handlePreview(voice.id)}
                disabled={previewPlaying === voice.id}
                className="p-3 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 transition-transform active:scale-95 flex items-center justify-center"
                title="Play Audio Sample"
              >
                {previewPlaying === voice.id ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Play className="h-5 w-5 fill-current" />
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
