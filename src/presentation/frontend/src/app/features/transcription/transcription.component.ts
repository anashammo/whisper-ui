import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranscriptionService } from '../../core/services/transcription.service';
import { Transcription, TranscriptionStatus } from '../../core/models/transcription.model';
import { PopupService } from '../../shared/services/popup.service';

/**
 * Transcription detail component
 */
@Component({
  selector: 'app-transcription',
  templateUrl: './transcription.component.html',
  styleUrls: ['./transcription.component.css']
})
export class TranscriptionComponent implements OnInit, OnDestroy {
  transcription: Transcription | null = null;
  isLoading: boolean = false;
  error: string | null = null;
  private destroy$ = new Subject<void>();
  isPlayingAudio: boolean = false;
  currentAudio: HTMLAudioElement | null = null;

  // Expose enum to template
  TranscriptionStatus = TranscriptionStatus;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    public transcriptionService: TranscriptionService,
    private popupService: PopupService
  ) {}

  ngOnInit(): void {
    // Get transcription ID from route
    const id = this.route.snapshot.paramMap.get('id');

    if (id) {
      this.loadTranscription(id);
    }

    // Subscribe to current transcription updates
    this.transcriptionService
      .getCurrentTranscription()
      .pipe(takeUntil(this.destroy$))
      .subscribe((transcription) => {
        this.transcription = transcription;
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
    // Stop any playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load transcription by ID
   */
  private loadTranscription(id: string): void {
    this.transcriptionService.loadTranscription(id);
  }

  /**
   * Play audio file for the transcription
   */
  playAudio(): void {
    // If already playing, do nothing (button will show stop instead)
    if (this.isPlayingAudio) {
      return;
    }

    if (!this.transcription?.id) {
      console.error('No transcription ID available');
      return;
    }

    // Stop any currently playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
    }

    const audioUrl = this.transcriptionService.getAudioUrl(this.transcription.id);
    console.log('Playing audio from:', audioUrl);

    this.currentAudio = new Audio(audioUrl);
    this.isPlayingAudio = true;
    this.error = null;

    this.currentAudio.addEventListener('loadeddata', () => {
      console.log('Audio loaded successfully, duration:', this.currentAudio?.duration);
    });

    this.currentAudio.addEventListener('error', (e: any) => {
      console.error('Audio playback error:', e);
      console.error('Error code:', this.currentAudio?.error?.code);
      console.error('Error message:', this.currentAudio?.error?.message);
      this.isPlayingAudio = false;
      this.error = 'Failed to play audio file';
    });

    this.currentAudio.addEventListener('ended', () => {
      console.log('Audio playback ended');
      this.isPlayingAudio = false;
    });

    this.currentAudio.addEventListener('pause', () => {
      console.log('Audio paused');
      this.isPlayingAudio = false;
    });

    this.currentAudio.play().then(() => {
      console.log('Audio playback started successfully');
    }).catch(err => {
      console.error('Play failed:', err);
      this.isPlayingAudio = false;
      this.error = 'Failed to play audio: ' + err.message;
    });
  }

  /**
   * Stop audio playback
   */
  stopAudio(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.isPlayingAudio = false;
  }

  /**
   * Copy transcription text to clipboard
   */
  copyToClipboard(): void {
    if (this.transcription?.text) {
      navigator.clipboard.writeText(this.transcription.text).then(() => {
        // Use custom success popup instead of browser alert
        this.popupService.success('Transcription copied to clipboard!')
          .pipe(takeUntil(this.destroy$))
          .subscribe();
      });
    }
  }

  /**
   * Download transcription as text file
   */
  downloadText(): void {
    if (!this.transcription?.text) return;

    const blob = new Blob([this.transcription.text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transcription-${this.transcription.id}.txt`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  /**
   * Navigate back to upload
   */
  goToUpload(): void {
    this.transcriptionService.clearCurrent();
    this.router.navigate(['/']);
  }

  /**
   * Navigate to history
   */
  goToHistory(): void {
    this.router.navigate(['/history']);
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString();
  }
}
