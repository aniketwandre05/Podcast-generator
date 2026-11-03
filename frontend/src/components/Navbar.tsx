import React from 'react';
import { Mic, Headphones, Volume2, Plus } from 'lucide-react';

interface NavbarProps {
  currentTab: 'create' | 'library' | 'voices';
  setCurrentTab: (tab: 'create' | 'library' | 'voices') => void;
  openCreateModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, openCreateModal }) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('library')}>
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Mic className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">PodcastAI</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Sarvam AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
              Multi-speaker Indic Audio Studio
            </p>
          </div>
        </div>

        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => setCurrentTab('library')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              currentTab === 'library'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Headphones className="h-4 w-4" />
            <span>Library</span>
          </button>

          <button
            onClick={() => setCurrentTab('voices')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              currentTab === 'voices'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Volume2 className="h-4 w-4" />
            <span>Voices</span>
          </button>

          <button
            onClick={openCreateModal}
            className="flex items-center space-x-2 px-4 py-1.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-md shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="h-4 w-4" />
            <span>New Episode</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
