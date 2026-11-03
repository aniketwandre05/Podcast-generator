import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertCircle, Sparkles, Mic, FileText, Music, Radio } from 'lucide-react';

interface ProgressViewerProps {
  episodeId: string;
  onComplete: () => void;
}

interface LogEntry {
  timestamp: string;
  message: string;
  status: string;
}

export const ProgressViewer: React.FC<ProgressViewerProps> = ({ episodeId, onComplete }) => {
  const [percent, setPercent] = useState(5);
  const [status, setStatus] = useState<string>('researching');
  const [message, setMessage] = useState<string>('Initializing pipeline...');
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    let isMounted = true;

    // 1. Initial status fetch to sync state immediately (even after page refresh)
    const fetchCurrentStatus = async () => {
      try {
        const res = await fetch(`/api/episodes/${episodeId}`);
        if (!res.ok || !isMounted) return;
        const data = await res.json();
        if (data.progress_percent !== undefined) setPercent(data.progress_percent);
        if (data.status) setStatus(data.status);
        if (data.status_message) setMessage(data.status_message);

        if (data.status === 'completed') {
          setPercent(100);
          setStatus('completed');
          setMessage('Episode generation complete!');
          setTimeout(() => {
            if (isMounted) onComplete();
          }, 800);
        } else if (data.status === 'failed') {
          setError(data.error_message || 'Episode generation failed.');
        }
      } catch (err) {
        console.error('Initial status fetch error', err);
      }
    };
    fetchCurrentStatus();

    // 2. Real-time Server-Sent Events (SSE) stream
    const eventSource = new EventSource(`/api/episodes/${episodeId}/events`);

    eventSource.addEventListener('progress', (e: any) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.percent !== undefined) setPercent(payload.percent);
        if (payload.status) setStatus(payload.status);
        if (payload.message) {
          setMessage(payload.message);
          setLogs((prev) => [
            {
              timestamp: new Date().toLocaleTimeString(),
              message: payload.message,
              status: payload.status,
            },
            ...prev.slice(0, 30),
          ]);
        }
      } catch (err) {
        console.error('SSE parse error', err);
      }
    });

    eventSource.addEventListener('completed', () => {
      setPercent(100);
      setStatus('completed');
      setMessage('Episode generation complete!');
      eventSource.close();
      setTimeout(() => {
        if (isMounted) onComplete();
      }, 1000);
    });

    eventSource.addEventListener('error', (e: any) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.error) setError(payload.error);
      } catch {
        // SSE reconnecting or silent timeout
      }
    });

    // 3. Fallback polling every 3 seconds to guarantee progress never hangs if SSE disconnects on Render
    const pollInterval = setInterval(async () => {
      if (!isMounted) return;
      try {
        const res = await fetch(`/api/episodes/${episodeId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.progress_percent !== undefined && data.progress_percent > percent) {
          setPercent(data.progress_percent);
        }
        if (data.status && data.status !== status) {
          setStatus(data.status);
        }
        if (data.status_message && data.status_message !== message) {
          setMessage(data.status_message);
          setLogs((prev) => [
            {
              timestamp: new Date().toLocaleTimeString(),
              message: data.status_message,
              status: data.status,
            },
            ...prev.slice(0, 30),
          ]);
        }

        if (data.status === 'completed') {
          setPercent(100);
          setStatus('completed');
          setMessage('Episode generation complete!');
          clearInterval(pollInterval);
          eventSource.close();
          setTimeout(() => {
            if (isMounted) onComplete();
          }, 800);
        } else if (data.status === 'failed') {
          setError(data.error_message || 'Pipeline failed.');
          clearInterval(pollInterval);
          eventSource.close();
        }
      } catch (err) {
        console.error('Polling sync error', err);
      }
    }, 3000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
      eventSource.close();
    };
  }, [episodeId, onComplete]);

  const steps = [
    { id: 'researching', label: 'Researching', icon: Radio },
    { id: 'outlining', label: 'Outlining', icon: FileText },
    { id: 'writing', label: 'Scriptwriting', icon: Sparkles },
    { id: 'synthesizing', label: 'Bulbul TTS', icon: Mic },
    { id: 'mixing', label: 'Mastering', icon: Music },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl max-w-3xl mx-auto my-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="h-3 w-3 rounded-full bg-indigo-500 animate-ping" />
          <h3 className="text-lg font-bold text-white">Generating Podcast Episode</h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
          {percent}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-3 mb-6 p-0.5 border border-slate-800 overflow-hidden">
        <div
          className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 h-full rounded-full transition-all duration-500 ease-out shadow-lg shadow-indigo-500/50"
          style={{ width: `${Math.max(5, percent)}%` }}
        />
      </div>

      {/* Step Badges */}
      <div className="grid grid-cols-5 gap-2 mb-6">
        {steps.map((st, idx) => {
          const Icon = st.icon;
          const isCurrent = status === st.id;
          const isDone = percent > (idx + 1) * 18;

          return (
            <div
              key={st.id}
              className={`p-2.5 rounded-xl border text-center transition-all ${
                isDone
                  ? 'bg-indigo-950/40 border-indigo-500/40 text-indigo-300'
                  : isCurrent
                  ? 'bg-slate-800 border-indigo-500 text-white shadow-md shadow-indigo-500/20'
                  : 'bg-slate-950 border-slate-800/80 text-slate-500'
              }`}
            >
              <div className="flex justify-center mb-1">
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>
              <p className="text-[11px] font-semibold truncate">{st.label}</p>
            </div>
          );
        })}
      </div>

      {/* Current Status Message */}
      <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
          <span className="text-sm font-medium text-slate-200">{message}</span>
        </div>
        <span className="text-xs text-slate-500 uppercase font-bold tracking-wider">Live Pipeline</span>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/50 rounded-xl text-rose-200 flex items-start space-x-3 mb-4">
          <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">Pipeline Error</p>
            <p className="text-xs text-rose-300/90">{error}</p>
          </div>
        </div>
      )}

      {/* Real-time Activity Logs */}
      <div>
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Live Activity Log</h4>
        <div className="bg-slate-950 rounded-xl p-3 border border-slate-800 max-h-40 overflow-y-auto font-mono text-xs space-y-1.5">
          {logs.map((log, index) => (
            <div key={index} className="flex items-center space-x-2 text-slate-400">
              <span className="text-slate-600">{log.timestamp}</span>
              <span className="text-indigo-400">[{log.status}]</span>
              <span className="text-slate-200">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && <p className="text-slate-600">Connecting to generation pipeline...</p>}
        </div>
      </div>
    </div>
  );
};
