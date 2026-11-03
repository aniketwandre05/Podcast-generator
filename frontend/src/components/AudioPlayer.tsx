import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, RotateCw, Download, FileText } from 'lucide-react';
import type { Episode } from '../types';

interface AudioPlayerProps {
  episode: Episode;
  onEditScript: () => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ episode, onEditScript }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(episode.duration_seconds || 0);
  const [volume, setVolume] = useState(0.9);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [exportOpen, setExportOpen] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration || episode.duration_seconds);
    };

    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [episode.duration_seconds]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setCurrentTime(val);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
    }
  };

  const handleSkip = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(duration, audioRef.current.currentTime + seconds));
    }
  };

  const cyclePlaybackRate = () => {
    const rates = [1.0, 1.25, 1.5, 2.0];
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const nextRate = rates[nextIdx];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };


  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const audioSrc = `/api/episodes/${episode.id}/export?format=wav`;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden mb-8">
      <audio ref={audioRef} src={audioSrc} preload="metadata" />

      {/* Header Info */}
      <div className="p-6 border-b border-slate-800/80 bg-gradient-to-r from-slate-900 via-indigo-950/20 to-slate-900">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1.5">
              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                {episode.language} • {episode.tone}
              </span>
              <span className="text-xs text-slate-400">
                {episode.speakers_config?.length || 2} Speakers (Bulbul:v3)
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white">{episode.title}</h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl line-clamp-2">
              {episode.description || episode.topic}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={onEditScript}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <FileText className="h-4 w-4 text-indigo-400" />
              <span>Edit Script</span>
            </button>

            {/* Export Dropdown */}
            <div className="relative">
              <button
                onClick={() => setExportOpen(!exportOpen)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export</span>
              </button>

              {exportOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-950 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 text-xs">
                  <a
                    href={`/api/episodes/${episode.id}/export?format=wav`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Master Audio (WAV)
                  </a>
                  <a
                    href={`/api/episodes/${episode.id}/export?format=mp3`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Broadcast Audio (MP3)
                  </a>
                  <a
                    href={`/api/episodes/${episode.id}/export?format=srt`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Subtitles (SRT)
                  </a>
                  <a
                    href={`/api/episodes/${episode.id}/export?format=vtt`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Web Subtitles (VTT)
                  </a>
                  <a
                    href={`/api/episodes/${episode.id}/export?format=md`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Show Notes (Markdown)
                  </a>
                  <a
                    href={`/api/episodes/${episode.id}/export?format=json`}
                    download
                    className="block px-4 py-2 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Script JSON
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Player Bar */}
      <div className="p-6 bg-slate-950">
        {/* Scrub Slider */}
        <div className="flex items-center space-x-3 mb-4">
          <span className="text-xs font-mono text-slate-400 w-10 text-right">{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <span className="text-xs font-mono text-slate-400 w-10">{formatTime(duration)}</span>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleSkip(-10)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
              title="Rewind 10s"
            >
              <RotateCcw className="h-4 w-4" />
            </button>

            <button
              onClick={togglePlay}
              className="p-3.5 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/30 transition-transform active:scale-95"
            >
              {isPlaying ? <Pause className="h-5 w-5 fill-current" /> : <Play className="h-5 w-5 fill-current ml-0.5" />}
            </button>

            <button
              onClick={() => handleSkip(10)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
              title="Fast Forward 10s"
            >
              <RotateCw className="h-4 w-4" />
            </button>

            <button
              onClick={cyclePlaybackRate}
              className="px-2 py-1 rounded-md text-xs font-bold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            >
              {playbackRate}x
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.muted = !isMuted;
                  setIsMuted(!isMuted);
                }
              }}
              className="p-2 text-slate-400 hover:text-white"
            >
              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                const v = parseFloat(e.target.value);
                setVolume(v);
                setIsMuted(false);
                if (audioRef.current) {
                  audioRef.current.volume = v;
                  audioRef.current.muted = false;
                }
              }}
              className="w-20 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
