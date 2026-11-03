export interface SourceItem {
  id?: string;
  source_type: 'file' | 'url' | 'youtube' | 'text';
  title: string;
  content: string;
  file_type?: string;
  file_size?: number;
  word_count?: number;
  author?: string;
  url?: string;
  has_transcript?: boolean;
}

export interface SpeakerConfig {
  speaker_id: string; // HOST, CO_HOST, GUEST
  display_name: string;
  voice: string; // shubh, priya, rohan, etc.
  gender?: string;
  pace: number;
  language_code: string;
}

export interface Turn {
  speaker: string;
  text: string;
  emotion?: string;
  pause_after_ms: number;
  language_code?: string;
}

export interface Segment {
  name: string;
  summary?: string;
  turns: Turn[];
}

export interface Script {
  title: string;
  description: string;
  segments: Segment[];
}

export interface OutlineSegment {
  title: string;
  goal: string;
  key_points: string[];
}

export interface Outline {
  title: string;
  hook: string;
  intro: string;
  segments: OutlineSegment[];
  recap: string;
  outro: string;
}

export interface Episode {
  id: string;
  title: string;
  description: string;
  topic: string;
  source_type: string;
  sources?: SourceItem[];
  language: string;
  dialogue_style?: string;
  tone: string;
  target_duration_mins: number;
  speakers_config: SpeakerConfig[];
  research_brief: {
    key_facts?: string[];
    key_points?: string[];
    interesting_angles?: string[];
    sources?: string[];
  };
  outline: Outline;
  script: Script;
  audio_path?: string;
  audio_url?: string;
  duration_seconds: number;
  status: 'created' | 'researching' | 'outlining' | 'writing' | 'synthesizing' | 'mixing' | 'completed' | 'failed';
  progress_percent: number;
  status_message: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Voice {
  id: string;
  name: string;
  gender: string;
  description: string;
  model: string;
}

export interface TurnTimestamp {
  speaker: string;
  text: string;
  start: number;
  end: number;
  duration: number;
}

