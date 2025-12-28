import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranscriptionService } from '../../core/services/transcription.service';
import { Transcription } from '../../core/models/transcription.model';
import { PopupService } from '../../shared/services/popup.service';

/**
 * History list component
 */
@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit, OnDestroy {
  transcriptions: Transcription[] = [];
  isLoading: boolean = false;
  error: string | null = null;
  private destroy$ = new Subject<void>();

  // Audio playback tracking
  currentlyPlayingId: string | null = null;
  currentAudio: HTMLAudioElement | null = null;

  constructor(
    public transcriptionService: TranscriptionService,
    private router: Router,
    private popupService: PopupService
  ) {}

  ngOnInit(): void {
    // Load transcription history
    this.loadHistory();

    // Subscribe to transcriptions list
    this.transcriptionService
      .getTranscriptions()
      .pipe(takeUntil(this.destroy$))
      .subscribe((transcriptions) => {
        this.transcriptions = transcriptions;
      });

    // Subscribe to loading state
    this.transcriptionService
      .getLoadingState()
      .pipe(takeUntil(this.destroy$))
      .subscribe((isLoading) => {
        this.isLoading = isLoading;
      });

    // Subscribe to errors
    this.transcriptionService
      .getError()
      .pipe(takeUntil(this.destroy$))
      .subscribe((error) => {
        this.error = error;
      });
  }

  ngOnDestroy(): void {
    // Stop and clean up audio playback
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load transcription history
   */
  loadHistory(): void {
    this.transcriptionService.loadHistory();
  }

  /**
   * Navigate to transcription detail
   */
  viewTranscription(id: string): void {
    this.router.navigate(['/transcription', id]);
  }

  /**
   * Navigate to upload
   */
  goToUpload(): void {
    this.router.navigate(['/']);
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  /**
   * Get truncated text preview
   */
  getTruncatedText(text: string | null, maxLength: number = 100): string {
    if (!text) return 'No text available';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }

  /**
   * Check if audio is currently playing for a specific transcription
   */
  isPlaying(transcriptionId: string): boolean {
    return this.currentlyPlayingId === transcriptionId;
  }

  /**
   * Play audio file for a transcription
   */
  playAudio(event: Event, transcriptionId: string): void {
    event.stopPropagation(); // Prevent card click event

    // If already playing this audio, do nothing (button will show stop instead)
    if (this.currentlyPlayingId === transcriptionId) {
      return;
    }

    // Stop any currently playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
    }

    const audioUrl = this.transcriptionService.getAudioUrl(transcriptionId);
    this.currentAudio = new Audio(audioUrl);
    this.currentlyPlayingId = transcriptionId;
    this.error = null;

    this.currentAudio.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      this.currentlyPlayingId = null;
      this.error = 'Failed to play audio file';
    });

    this.currentAudio.addEventListener('ended', () => {
      this.currentlyPlayingId = null;
    });

    this.currentAudio.addEventListener('pause', () => {
      this.currentlyPlayingId = null;
    });

    this.currentAudio.play().catch(err => {
      console.error('Play failed:', err);
      this.currentlyPlayingId = null;
      this.error = 'Failed to play audio: ' + err.message;
    });
  }

  /**
   * Stop audio playback
   */
  stopAudio(event: Event): void {
    event.stopPropagation(); // Prevent card click event

    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.currentlyPlayingId = null;
  }

  /**
   * Delete a transcription
   */
  deleteTranscription(event: Event, transcriptionId: string): void {
    event.stopPropagation(); // Prevent card click event

    // Use custom popup instead of browser confirm
    this.popupService.confirm(
      'Delete Transcription',
      'Are you sure you want to delete this transcription? This action cannot be undone.',
      'Delete',
      'Cancel'
    ).pipe(takeUntil(this.destroy$))
    .subscribe((confirmed) => {
      if (!confirmed) {
        return;
      }

      this.transcriptionService.deleteTranscription(transcriptionId).subscribe({
        next: () => {
          console.log(`Transcription ${transcriptionId} deleted successfully`);
        },
        error: (error) => {
          console.error('Delete failed:', error);
          this.error = 'Failed to delete transcription: ' + error.message;
        }
      });
    });
  }
}
