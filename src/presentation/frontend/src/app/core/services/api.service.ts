import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Transcription, TranscriptionListResponse } from '../models/transcription.model';

/**
 * API service for HTTP communication with the backend
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Upload and transcribe an audio file
   */
  uploadAudio(file: File, language?: string, model?: string, enableLlmEnhancement?: boolean, vadFilter?: boolean, enableTashkeel?: boolean): Observable<Transcription> {
    const formData = new FormData();
    formData.append('file', file);

    let params = new HttpParams();
    if (language) {
      params = params.set('language', language);
    }
    if (model) {
      params = params.set('model', model);
    }
    if (enableLlmEnhancement !== undefined) {
      params = params.set('enable_llm_enhancement', enableLlmEnhancement.toString());
    }
    if (vadFilter !== undefined) {
      params = params.set('vad_filter', vadFilter.toString());
    }
    if (enableTashkeel !== undefined) {
      params = params.set('enable_tashkeel', enableTashkeel.toString());
    }

    return this.http.post<Transcription>(
      `${this.apiUrl}/transcriptions`,
      formData,
      { params }
    );
  }

  /**
   * Get paginated transcription history
   */
  getTranscriptions(limit: number = 100, offset: number = 0): Observable<TranscriptionListResponse> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    return this.http.get<TranscriptionListResponse>(
      `${this.apiUrl}/transcriptions`,
      { params }
    );
  }

  /**
   * Get specific transcription by ID
   */
  getTranscription(id: string): Observable<Transcription> {
    return this.http.get<Transcription>(
      `${this.apiUrl}/transcriptions/${id}`
    );
  }

  /**
   * Re-transcribe an existing audio file with a different model
   */
  retranscribeAudio(audioFileId: string, model: string, language?: string, enableLlmEnhancement?: boolean, vadFilter?: boolean, enableTashkeel?: boolean): Observable<Transcription> {
    let params = new HttpParams().set('model', model);
    if (language) {
      params = params.set('language', language);
    }
    if (enableLlmEnhancement !== undefined) {
      params = params.set('enable_llm_enhancement', enableLlmEnhancement.toString());
    }
    if (vadFilter !== undefined) {
      params = params.set('vad_filter', vadFilter.toString());
    }
    if (enableTashkeel !== undefined) {
      params = params.set('enable_tashkeel', enableTashkeel.toString());
    }

    return this.http.post<Transcription>(
      `${this.apiUrl}/audio-files/${audioFileId}/transcriptions`,
      null,
      { params }
    );
  }

  /**
   * Enhance transcription with LLM
   */
  enhanceTranscription(transcriptionId: string): Observable<Transcription> {
    return this.http.post<Transcription>(
      `${this.apiUrl}/transcriptions/${transcriptionId}/enhance`,
      null
    );
  }

  /**
   * Get all transcriptions for a specific audio file
   */
  getAudioFileTranscriptions(audioFileId: string): Observable<Transcription[]> {
    return this.http.get<Transcription[]>(
      `${this.apiUrl}/audio-files/${audioFileId}/transcriptions`
    );
  }

  /**
   * Check API health
   */
  healthCheck(): Observable<{ status: string; message: string }> {
    return this.http.get<{ status: string; message: string }>(
      `${this.apiUrl}/health`
    );
  }

  /**
   * Get system information
   */
  getSystemInfo(): Observable<any> {
    return this.http.get(`${this.apiUrl}/info`);
  }

  /**
   * Delete a transcription
   */
  deleteTranscription(id: string): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/transcriptions/${id}`
    );
  }

  /**
   * Delete an audio file and all associated transcriptions
   */
  deleteAudioFile(audioFileId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/audio-files/${audioFileId}`
    );
  }

  /**
   * Get audio file URL for a transcription
   */
  getAudioUrl(id: string): string {
    return `${this.apiUrl}/transcriptions/${id}/audio`;
  }

  /**
   * Get audio file download URL with download parameter
   * This triggers browser download instead of inline playback
   */
  getAudioDownloadUrl(id: string): string {
    return `${this.apiUrl}/transcriptions/${id}/audio?download=true`;
  }

  /**
   * Check model status (cached, loaded, downloading)
   */
  getModelStatus(modelName: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/models/status/${modelName}`);
  }

  /**
   * Get SSE stream URL for model download progress
   */
  getModelProgressUrl(modelName: string): string {
    return `${this.apiUrl}/models/download-progress/${modelName}`;
  }

  /**
   * Get list of available models
   */
  getAvailableModels(): Observable<any> {
    return this.http.get(`${this.apiUrl}/models/available`);
  }
}
