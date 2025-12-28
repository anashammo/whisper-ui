import { Transcription } from './transcription.model';

/**
 * Audio file model matching the API response schema
 */
export interface AudioFile {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  duration_seconds: number | null;
  uploaded_at: string;
}

/**
 * Audio file with all its transcriptions (grouped view)
 */
export interface AudioFileWithTranscriptions {
  audio_file: AudioFile;
  transcriptions: Transcription[];
  transcription_count: number;
}
