import React from 'react';
import { Play, Copy, Trash2, Clock, Volume2, Plus, Sparkles } from 'lucide-react';
import type { Episode } from '../types';

interface EpisodeLibraryProps {
  episodes: Episode[];
  onSelectEpisode: (ep: Episode) => void;
  onOpenCreate: () => void;
  onDeleteEpisode: (id: string) => void;
  onDuplicateEpisode: (id: string) => void;
}

export const EpisodeLibrary: React.FC<EpisodeLibraryProps> = ({
  episodes,
  onSelectEpisode,
  onOpenCreate,
  onDeleteEpisode,
  onDuplicateEpisode,
}) => {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  if (episodes.length === 0) {
    return (
      <div className="max-w-4xl mx-auto my-16 px-4 text-center">
        <div className="h-16 w-16 mx-auto mb-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <Volume2 className="h-8 w-8" />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No episodes generated yet</h3>
        <p className="text-sm text-slate-400 mb-6 max-w-md mx-auto">
          Create your first AI podcast episode from a topic, document, or webpage with Sarvam AI's multi-speaker voices.
        </p>
        <button
          onClick={onOpenCreate}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25"
        >
          <Sparkles className="h-4 w-4" />
          <span>Generate First Episode</span>
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Episode Library</h2>
          <p className="text-xs text-slate-400">All generated shows, master audio, and show notes</p>
        </div>
        <button
          onClick={onOpenCreate}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-500/20"
        >
          <Plus className="h-4 w-4" />
          <span>New Episode</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {episodes.map((ep) => (
          <div
            key={ep.id}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] px-2 py-0.5 rounded-full font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase">
                  {ep.language} • {ep.tone}
                </span>

                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                    ep.status === 'completed'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : ep.status === 'failed'
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse'
                  }`}
                >
                  {ep.status}
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5 line-clamp-1">{ep.title}</h3>
              <p className="text-xs text-slate-400 line-clamp-2 mb-4">{ep.description || ep.topic}</p>
            </div>

            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-500 pb-3 mb-3 border-b border-slate-800">
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{formatDuration(ep.duration_seconds || 0)}</span>
                </div>
                <span>{new Date(ep.created_at).toLocaleDateString()}</span>
              </div>

              <div className="flex items-center justify-between">
                <button
                  onClick={() => onSelectEpisode(ep)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Open & Listen</span>
                </button>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => onDuplicateEpisode(ep.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                    title="Duplicate Episode"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => onDeleteEpisode(ep.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                    title="Delete Episode"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
