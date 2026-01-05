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
  processing_time_seconds: number | null;

  // LLM Enhancement fields
  enable_llm_enhancement: boolean;
  enhanced_text: string | null;
  llm_processing_time_seconds: number | null;
  llm_enhancement_status: string | null;
  llm_error_message: string | null;

  // Voice Activity Detection (VAD) field
  vad_filter_used: boolean;

  // Arabic Tashkeel (Diacritization) field
  enable_tashkeel: boolean;
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
