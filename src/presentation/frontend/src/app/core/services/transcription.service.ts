import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval } from 'rxjs';
import { switchMap, takeWhile, tap } from 'rxjs/operators';
import { ApiService } from './api.service';
import { Transcription, TranscriptionStatus } from '../models/transcription.model';

/**
 * Transcription service with business logic
 */
@Injectable({
  providedIn: 'root'
})
export class TranscriptionService {
  private currentTranscription$ = new BehaviorSubject<Transcription | null>(null);
  private transcriptions$ = new BehaviorSubject<Transcription[]>([]);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);

  constructor(private apiService: ApiService) {}

  /**
   * Get current transcription observable
   */
  getCurrentTranscription(): Observable<Transcription | null> {
    return this.currentTranscription$.asObservable();
  }

  /**
   * Get transcriptions list observable
   */
  getTranscriptions(): Observable<Transcription[]> {
    return this.transcriptions$.asObservable();
  }

  /**
   * Get loading state observable
   */
  getLoadingState(): Observable<boolean> {
    return this.isLoading$.asObservable();
  }

  /**
   * Get error observable
   */
  getError(): Observable<string | null> {
    return this.error$.asObservable();
  }

  /**
   * Upload and transcribe audio file
   */
  uploadAudio(file: File, language?: string, model?: string): Observable<Transcription> {
    this.isLoading$.next(true);
    this.error$.next(null);

    return this.apiService.uploadAudio(file, language, model).pipe(
      tap({
        next: (transcription) => {
          this.currentTranscription$.next(transcription);
          this.isLoading$.next(false);

          // If transcription is processing, poll for updates
          if (transcription.status === TranscriptionStatus.PROCESSING ||
              transcription.status === TranscriptionStatus.PENDING) {
            this.pollTranscriptionStatus(transcription.id);
          }
        },
        error: (error) => {
          this.error$.next(error.error?.detail || 'Upload failed');
          this.isLoading$.next(false);
        }
      })
    );
  }

  /**
   * Poll transcription status until completed or failed
   */
  private pollTranscriptionStatus(id: string): void {
    interval(2000) // Poll every 2 seconds
      .pipe(
        switchMap(() => this.apiService.getTranscription(id)),
        takeWhile(
          (transcription) =>
            transcription.status === TranscriptionStatus.PROCESSING ||
            transcription.status === TranscriptionStatus.PENDING,
          true // Include the final value
        ),
        tap((transcription) => {
          this.currentTranscription$.next(transcription);
        })
      )
      .subscribe();
  }

  /**
   * Load transcription history
   */
  loadHistory(limit: number = 100, offset: number = 0): void {
    this.isLoading$.next(true);
    this.error$.next(null);

    this.apiService.getTranscriptions(limit, offset).subscribe({
      next: (response) => {
        this.transcriptions$.next(response.items);
        this.isLoading$.next(false);
      },
      error: (error) => {
        this.error$.next(error.error?.detail || 'Failed to load history');
        this.isLoading$.next(false);
      }
    });
  }

  /**
   * Load specific transcription
   */
  loadTranscription(id: string): void {
    this.isLoading$.next(true);
    this.error$.next(null);

    this.apiService.getTranscription(id).subscribe({
      next: (transcription) => {
        this.currentTranscription$.next(transcription);
        this.isLoading$.next(false);
      },
      error: (error) => {
        this.error$.next(error.error?.detail || 'Failed to load transcription');
        this.isLoading$.next(false);
      }
    });
  }

  /**
   * Clear current transcription
   */
  clearCurrent(): void {
    this.currentTranscription$.next(null);
  }

  /**
   * Clear error
   */
  clearError(): void {
    this.error$.next(null);
  }

  /**
   * Get status badge class
   */
  getStatusClass(status: TranscriptionStatus): string {
    switch (status) {
      case TranscriptionStatus.COMPLETED:
        return 'status-completed';
      case TranscriptionStatus.PROCESSING:
        return 'status-processing';
      case TranscriptionStatus.PENDING:
        return 'status-pending';
      case TranscriptionStatus.FAILED:
        return 'status-failed';
      default:
        return '';
    }
  }

  /**
   * Format duration in seconds to readable format
   */
  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Delete a transcription
   */
  deleteTranscription(id: string): Observable<void> {
    return this.apiService.deleteTranscription(id).pipe(
      tap({
        next: () => {
          // Remove from local list
          const currentList = this.transcriptions$.value;
          const updatedList = currentList.filter(t => t.id !== id);
          this.transcriptions$.next(updatedList);
        },
        error: (error) => {
          this.error$.next(error.error?.detail || 'Failed to delete transcription');
        }
      })
    );
  }

  /**
   * Get audio URL for a transcription
   */
  getAudioUrl(id: string): string {
    return this.apiService.getAudioUrl(id);
  }
}
