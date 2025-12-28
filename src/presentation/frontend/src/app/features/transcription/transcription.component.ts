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
  transcription: Transcription | null = null; // Currently loaded transcription (from route)
  allTranscriptions: Transcription[] = []; // All transcriptions for this audio file
  activeTranscription: Transcription | null = null; // Currently selected tab
  isLoading: boolean = false;
  error: string | null = null;
  private destroy$ = new Subject<void>();
  isPlayingAudio: boolean = false;
  currentAudio: HTMLAudioElement | null = null;

  // Re-transcription modal state
  showRetranscribeDialog: boolean = false;
  selectedModel: string = 'base';
  availableModels: string[] = ['tiny', 'base', 'small', 'medium', 'large'];
  isRetranscribing: boolean = false;

  // Model information
  modelInfo: { [key: string]: { name: string; description: string; params: string; speed: string } } = {
    'tiny': {
      name: 'Tiny',
      description: 'Fastest model, suitable for quick transcriptions with acceptable accuracy',
      params: '39M parameters',
      speed: 'Very Fast'
    },
    'base': {
      name: 'Base',
      description: 'Good balance of speed and accuracy, recommended for most uses',
      params: '74M parameters',
      speed: 'Fast'
    },
    'small': {
      name: 'Small',
      description: 'Balanced speed and accuracy, better quality than base',
      params: '244M parameters',
      speed: 'Medium'
    },
    'medium': {
      name: 'Medium',
      description: 'Better accuracy than small, suitable for important transcriptions',
      params: '769M parameters',
      speed: 'Slow'
    },
    'large': {
      name: 'Large',
      description: 'Best accuracy available, recommended for critical transcriptions',
      params: '1550M parameters',
      speed: 'Very Slow'
    }
  };

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

        // When initial transcription loads, load all transcriptions for this audio file
        if (transcription && this.allTranscriptions.length === 0) {
          this.loadAllTranscriptions(transcription.audio_file_id);
        }

        // Set as active transcription if not already set
        if (transcription && !this.activeTranscription) {
          this.activeTranscription = transcription;
        }
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

    if (!this.activeTranscription?.id) {
      console.error('No active transcription ID available');
      return;
    }

    // Stop any currently playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
    }

    const audioUrl = this.transcriptionService.getAudioUrl(this.activeTranscription.id);
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
    if (this.activeTranscription?.text) {
      navigator.clipboard.writeText(this.activeTranscription.text).then(() => {
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
    if (!this.activeTranscription?.text) return;

    const blob = new Blob([this.activeTranscription.text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transcription-${this.activeTranscription.id}.txt`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  /**
   * Load all transcriptions for an audio file
   */
  private loadAllTranscriptions(audioFileId: string): void {
    this.transcriptionService.loadAudioFileTranscriptions(audioFileId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (transcriptions) => {
          this.allTranscriptions = transcriptions;
          // Update active transcription to match current transcription in the list
          if (this.transcription) {
            const current = transcriptions.find(t => t.id === this.transcription!.id);
            if (current) {
              this.activeTranscription = current;
            }
          }
        },
        error: (err) => {
          console.error('Failed to load all transcriptions:', err);
          // Still keep the single transcription if loading all fails
        }
      });
  }

  /**
   * Switch to a different transcription tab
   */
  switchTranscription(transcription: Transcription): void {
    // Stop any playing audio
    this.stopAudio();

    // Update active transcription
    this.activeTranscription = transcription;

    // Update URL without reloading the page
    this.router.navigate(['/transcription', transcription.id], { replaceUrl: true });
  }

  /**
   * Open re-transcription dialog
   */
  openRetranscribeDialog(): void {
    // Set default model to one not yet used
    const usedModels = this.allTranscriptions.map(t => t.model).filter(m => m !== null) as string[];
    const unused = this.availableModels.find(m => !usedModels.includes(m));
    this.selectedModel = unused || 'base';

    this.showRetranscribeDialog = true;
  }

  /**
   * Close re-transcription dialog
   */
  closeRetranscribeDialog(): void {
    this.showRetranscribeDialog = false;
    this.selectedModel = 'base';
    this.isRetranscribing = false;
  }

  /**
   * Submit re-transcription request
   */
  submitRetranscription(): void {
    if (!this.activeTranscription || !this.selectedModel) {
      return;
    }

    // Check if this model already exists
    const existingModel = this.allTranscriptions.find(t => t.model === this.selectedModel);
    if (existingModel) {
      this.popupService.alert(
        'Model Already Used',
        `A transcription with model "${this.selectedModel}" already exists. Please select a different model.`
      ).pipe(takeUntil(this.destroy$)).subscribe();
      return;
    }

    this.isRetranscribing = true;
    this.error = null;

    this.transcriptionService.retranscribeAudio(
      this.activeTranscription.audio_file_id,
      this.selectedModel,
      this.activeTranscription.language || undefined
    ).pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (newTranscription) => {
        // Add to all transcriptions list
        this.allTranscriptions.push(newTranscription);
        // Switch to new transcription tab
        this.switchTranscription(newTranscription);
        // Close dialog
        this.closeRetranscribeDialog();

        this.popupService.success(
          `Transcription with model "${this.selectedModel}" started successfully!`
        ).pipe(takeUntil(this.destroy$)).subscribe();
      },
      error: (err) => {
        console.error('Re-transcription failed:', err);
        const errorMessage = err.error?.detail || 'Failed to start re-transcription';
        this.error = errorMessage;
        this.isRetranscribing = false;

        this.popupService.error(
          errorMessage
        ).pipe(takeUntil(this.destroy$)).subscribe();
      }
    });
  }

  /**
   * Get list of models not yet transcribed
   */
  getModelsNotYetTranscribed(): string[] {
    const usedModels = this.allTranscriptions.map(t => t.model).filter(m => m !== null) as string[];
    return this.availableModels.filter(m => !usedModels.includes(m));
  }

  /**
   * Check if a model has already been transcribed
   */
  isModelAlreadyTranscribed(model: string): boolean {
    return this.allTranscriptions.some(t => t.model === model);
  }

  /**
   * Get information for the currently selected model
   */
  getSelectedModelInfo(): { name: string; description: string; params: string; speed: string } | null {
    return this.modelInfo[this.selectedModel] || null;
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
