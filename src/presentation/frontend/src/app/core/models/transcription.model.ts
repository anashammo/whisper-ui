/**
 * Transcription model matching the API response schema
 */
export interface Transcription {
  id: string;
  audio_file_id: string;
  text: string | null;
  status: TranscriptionStatus;
  language: string | null;
  duration_seconds: number;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  model: string | null;
  audio_file_original_filename: string | null;
  audio_file_uploaded_at: string | null;
}

/**
 * Transcription status enum
 */
export enum TranscriptionStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

/**
 * Paginated transcription list response
 */
export interface TranscriptionListResponse {
  items: Transcription[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  error_type?: string;
}
