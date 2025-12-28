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
  uploadAudio(file: File, language?: string, model?: string): Observable<Transcription> {
    const formData = new FormData();
    formData.append('file', file);

    let params = new HttpParams();
    if (language) {
      params = params.set('language', language);
    }
    if (model) {
      params = params.set('model', model);
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
   * Get audio file URL for a transcription
   */
  getAudioUrl(id: string): string {
    return `${this.apiUrl}/transcriptions/${id}/audio`;
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
