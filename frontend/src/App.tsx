import { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { CreateEpisodeModal } from './components/CreateEpisodeModal';
import { ProgressViewer } from './components/ProgressViewer';
import { AudioPlayer } from './components/AudioPlayer';
import { ScriptEditor } from './components/ScriptEditor';
import { EpisodeLibrary } from './components/EpisodeLibrary';
import { VoiceCatalogModal } from './components/VoiceCatalogModal';
import type { Episode } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<'create' | 'library' | 'voices'>('library');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [activeEpisodeId, setActiveEpisodeId] = useState<string | null>(null);
  const [activeEpisode, setActiveEpisode] = useState<Episode | null>(null);
  const [viewingScript, setViewingScript] = useState(false);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchEpisodes = () => {
    fetch('/api/episodes')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setEpisodes(data || []))
      .catch((e) => console.error('Error fetching episodes', e));
  };

  useEffect(() => {
    fetchEpisodes();
  }, [refreshTrigger]);

  useEffect(() => {
    if (activeEpisodeId) {
      fetch(`/api/episodes/${activeEpisodeId}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setActiveEpisode(data);
        });
    }
  }, [activeEpisodeId, refreshTrigger]);

  const handleEpisodeCreated = (id: string) => {
    setActiveEpisodeId(id);
    setViewingScript(false);
    setRefreshTrigger((prev) => prev + 1);
  };

  const handlePipelineComplete = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleDeleteEpisode = async (id: string) => {
    if (!confirm('Are you sure you want to delete this episode?')) return;
    try {
      await fetch(`/api/episodes/${id}`, { method: 'DELETE' });
      if (activeEpisodeId === id) {
        setActiveEpisodeId(null);
        setActiveEpisode(null);
      }
      setRefreshTrigger((prev) => prev + 1);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDuplicateEpisode = async (id: string) => {
    try {
      const res = await fetch(`/api/episodes/${id}/duplicate`, { method: 'POST' });
      const data = await res.json();
      if (data.id) {
        setActiveEpisodeId(data.id);
        setRefreshTrigger((prev) => prev + 1);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          setCurrentTab(tab);
          if (tab === 'library') {
            setActiveEpisodeId(null);
            setViewingScript(false);
          }
        }}
        openCreateModal={() => setCreateModalOpen(true)}
      />

      <main className="flex-1">
        {/* Create Modal */}
        <CreateEpisodeModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          onCreated={handleEpisodeCreated}
        />

        {/* Voices Tab */}
        {currentTab === 'voices' && <VoiceCatalogModal />}

        {/* Active Generation Pipeline Progress */}
        {activeEpisode && activeEpisode.status !== 'completed' && activeEpisode.status !== 'failed' && (
          <ProgressViewer
            episodeId={activeEpisode.id}
            onComplete={handlePipelineComplete}
          />
        )}

        {/* Script Editor View */}
        {viewingScript && activeEpisode && (
          <ScriptEditor
            episode={activeEpisode}
            onBack={() => setViewingScript(false)}
            onUpdated={() => {
              setViewingScript(false);
              setRefreshTrigger((prev) => prev + 1);
            }}
          />
        )}

        {/* Completed Episode Audio Player & Show Notes */}
        {!viewingScript && activeEpisode && activeEpisode.status === 'completed' && (
          <div className="max-w-6xl mx-auto my-8 px-4">
            <AudioPlayer
              episode={activeEpisode}
              onEditScript={() => setViewingScript(true)}
            />

            {/* Show Notes Preview */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Episode Synopsis & Discussion Points</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-300">
                <div>
                  <h4 className="font-semibold text-indigo-400 uppercase tracking-wider mb-2">Key Facts</h4>
                  <ul className="list-disc pl-4 space-y-1.5 text-slate-300">
                    {activeEpisode.research_brief?.key_facts?.map((f, i) => (
                      <li key={i}>{f}</li>
                    )) || <li>Grounded factual analysis from provided input.</li>}
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-400 uppercase tracking-wider mb-2">Discussion Angles</h4>
                  <ul className="list-disc pl-4 space-y-1.5 text-slate-300">
                    {activeEpisode.research_brief?.key_points?.map((p, i) => (
                      <li key={i}>{p}</li>
                    )) || <li>Insightful dialogue between speakers.</li>}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Episode Library View */}
        {currentTab === 'library' && !activeEpisodeId && (
          <EpisodeLibrary
            episodes={episodes}
            onSelectEpisode={(ep) => {
              setActiveEpisodeId(ep.id);
              setActiveEpisode(ep);
            }}
            onOpenCreate={() => setCreateModalOpen(true)}
            onDeleteEpisode={handleDeleteEpisode}
            onDuplicateEpisode={handleDuplicateEpisode}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        PodcastAI — Powered by Sarvam AI (Sarvam-M LLMs, Bulbul Text-to-Speech & Mayura Translate)
      </footer>
    </div>
  );
}

export default App;
