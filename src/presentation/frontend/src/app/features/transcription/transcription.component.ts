import { Component, OnInit, OnDestroy, NgZone } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranscriptionService } from '../../core/services/transcription.service';
import { Transcription, TranscriptionStatus } from '../../core/models/transcription.model';
import { PopupService } from '../../shared/services/popup.service';
import { ApiService } from '../../core/services/api.service';

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
  availableModels: string[] = ['tiny', 'base', 'small', 'medium', 'large', 'turbo'];
  isRetranscribing: boolean = false;
  enableLlmEnhancement: boolean = false;

  // LLM Enhancement state
  isEnhancing: boolean = false;

  // Model download progress
  isDownloadingModel: boolean = false;
  downloadProgress: number = 0;
  downloadStatus: string = '';
  progressEventSource: EventSource | null = null;

  // Model information - unified descriptions matching backend configuration
  modelInfo: { [key: string]: { name: string; description: string; params: string; speed: string } } = {
    'tiny': {
      name: 'Tiny',
      description: 'Fastest model with acceptable accuracy, ideal for quick drafts and testing',
      params: '39M parameters',
      speed: '~10x faster'
    },
    'base': {
      name: 'Base',
      description: 'Recommended for general use, excellent balance of speed and accuracy',
      params: '74M parameters',
      speed: '~7x faster'
    },
    'small': {
      name: 'Small',
      description: 'Balanced performance with better accuracy than base model',
      params: '244M parameters',
      speed: '~4x faster'
    },
    'medium': {
      name: 'Medium',
      description: 'High accuracy model suitable for important transcriptions',
      params: '769M parameters',
      speed: '~2x faster'
    },
    'large': {
      name: 'Large',
      description: 'Best accuracy available, recommended for critical transcriptions',
      params: '1550M parameters',
      speed: '1x (baseline)'
    },
    'turbo': {
      name: 'Turbo',
      description: 'Optimized for speed and accuracy, excellent all-around performance',
      params: '809M parameters',
      speed: '~8x faster'
    }
  };

  // Expose enum to template
  TranscriptionStatus = TranscriptionStatus;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    public transcriptionService: TranscriptionService,
    private popupService: PopupService,
    private apiService: ApiService,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    console.log('[TranscriptionComponent] ngOnInit - Component initialized/reloaded');

    // Get transcription ID from route
    const id = this.route.snapshot.paramMap.get('id');
    console.log('[TranscriptionComponent] Route ID:', id);

    if (id) {
      this.loadTranscription(id);
    }

    // Subscribe to current transcription updates
    this.transcriptionService
      .getCurrentTranscription()
      .pipe(takeUntil(this.destroy$))
      .subscribe((transcription) => {
        console.log('[TranscriptionComponent] Transcription updated:', transcription);
        this.transcription = transcription;

        // Always load all transcriptions for this audio file when transcription changes
        if (transcription) {
          // Check if we need to reload (different audio file or first load)
          const currentAudioFileId = this.allTranscriptions[0]?.audio_file_id;
          if (!currentAudioFileId || currentAudioFileId !== transcription.audio_file_id || this.allTranscriptions.length === 0) {
            console.log('[TranscriptionComponent] Loading all transcriptions for audio file:', transcription.audio_file_id);
            this.loadAllTranscriptions(transcription.audio_file_id);
          }

          // Set as active transcription if not already set or if it's a different transcription
          if (!this.activeTranscription || this.activeTranscription.id !== transcription.id) {
            this.activeTranscription = transcription;
          }
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
    console.log('[TranscriptionComponent] ngOnDestroy - Component being destroyed');

    // Stop any playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    // Close progress stream
    this.closeProgressStream();

    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Get CSS class for LLM enhancement status badge
   */
  getLLMStatusBadgeClass(): string {
    if (!this.activeTranscription || !this.activeTranscription.enable_llm_enhancement) {
      return 'llm-status-badge llm-not-enabled';
    }

    switch (this.activeTranscription.llm_enhancement_status) {
      case 'completed':
        return 'llm-status-badge llm-completed';
      case 'processing':
        return 'llm-status-badge llm-processing';
      case 'failed':
        return 'llm-status-badge llm-failed';
      default:
        return 'llm-status-badge llm-not-started';
    }
  }

  /**
   * Get display text for LLM enhancement badge
   */
  getLLMStatusText(): string {
    if (!this.activeTranscription || !this.activeTranscription.enable_llm_enhancement) {
      return '';
    }

    switch (this.activeTranscription.llm_enhancement_status) {
      case 'completed':
        return '✨ Enhanced';
      case 'processing':
        return '✨ Processing';
      case 'failed':
        return '✨ Failed';
      default:
        return '✨ Pending';
    }
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
   * Download audio file for current transcription
   * Creates a temporary anchor element to trigger browser download
   */
  downloadAudio(): void {
    if (!this.transcription) {
      console.error('No transcription available for download');
      return;
    }

    try {
      // Get download URL with download=true parameter
      const downloadUrl = this.transcriptionService.getAudioDownloadUrl(this.transcription.id);

      // Create temporary anchor element
      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.style.display = 'none';

      // Append to body, click, then remove
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);

      console.log(`Initiated download for transcription ${this.transcription.id}`);
    } catch (err) {
      console.error('Download failed:', err);
      this.error = 'Failed to download audio file';
    }
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
   * Copy enhanced transcription text to clipboard
   */
  copyEnhancedToClipboard(): void {
    if (this.activeTranscription?.enhanced_text) {
      navigator.clipboard.writeText(this.activeTranscription.enhanced_text).then(() => {
        // Use custom success popup instead of browser alert
        this.popupService.success('Enhanced transcription copied to clipboard!')
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
   * Get model size order for sorting (smaller to larger)
   */
  private getModelSizeOrder(model: string | null): number {
    const modelOrder: { [key: string]: number } = {
      'tiny': 0,
      'base': 1,
      'small': 2,
      'medium': 3,
      'large': 4,
      'turbo': 5
    };
    return model ? (modelOrder[model] ?? 999) : 999;
  }

  /**
   * Load all transcriptions for an audio file
   * @param audioFileId - The audio file ID
   * @param switchToId - Optional: ID of transcription to switch to after loading
   */
  private loadAllTranscriptions(audioFileId: string, switchToId?: string): void {
    console.log('[TranscriptionComponent] loadAllTranscriptions - Loading for audio file:', audioFileId);
    this.transcriptionService.loadAudioFileTranscriptions(audioFileId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (transcriptions) => {
          console.log('[TranscriptionComponent] Loaded transcriptions:', transcriptions);
          // Sort transcriptions by model size (smaller to larger)
          this.allTranscriptions = transcriptions.sort((a, b) =>
            this.getModelSizeOrder(a.model) - this.getModelSizeOrder(b.model)
          );
          console.log('[TranscriptionComponent] After sorting:', this.allTranscriptions.map(t => t.model));
          console.log('[TranscriptionComponent] Total transcriptions:', this.allTranscriptions.length);

          // If we need to switch to a specific transcription after loading
          if (switchToId) {
            const targetTranscription = this.allTranscriptions.find(t => t.id === switchToId);
            if (targetTranscription) {
              this.activeTranscription = targetTranscription;
              // Update URL to reflect the active transcription
              const url = this.router.createUrlTree(['/transcription', targetTranscription.id]).toString();
              window.history.replaceState({}, '', url);
              console.log('[TranscriptionComponent] Switched to new transcription and updated URL');
            }
          }
          // Otherwise, update active transcription to match current transcription in the list
          else if (this.transcription) {
            const current = transcriptions.find(t => t.id === this.transcription!.id);
            if (current) {
              this.activeTranscription = current;
            }
          }
        },
        error: (err) => {
          console.error('[TranscriptionComponent] Failed to load all transcriptions:', err);
          // Still keep the single transcription if loading all fails
        }
      });
  }

  /**
   * Switch to a different transcription tab
   */
  switchTranscription(transcription: Transcription): void {
    console.log('[TranscriptionComponent] switchTranscription - Switching to:', transcription.id, transcription.model);

    // Stop any playing audio
    this.stopAudio();

    // Update active transcription
    this.activeTranscription = transcription;

    // Update URL without triggering navigation/reload
    // Using window.history.replaceState to avoid component re-initialization
    const url = this.router.createUrlTree(['/transcription', transcription.id]).toString();
    console.log('[TranscriptionComponent] Updating URL to:', url);
    window.history.replaceState({}, '', url);
    console.log('[TranscriptionComponent] URL updated without reload');
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

    // Check if the default selected model needs to be downloaded
    this.checkModelStatus(this.selectedModel);
  }

  /**
   * Called when user selects a different model in the re-transcription dialog
   */
  onModelChange(): void {
    console.log('[TranscriptionComponent] Model changed to:', this.selectedModel);
    this.checkModelStatus(this.selectedModel);
  }

  /**
   * Check if model is cached and start progress tracking if downloading
   */
  checkModelStatus(modelName: string): void {
    this.apiService.getModelStatus(modelName).subscribe({
      next: (status) => {
        console.log('[TranscriptionComponent] Model status:', status);

        if (status.is_cached || status.is_loaded) {
          console.log('[TranscriptionComponent] Model is cached/loaded');
          this.isDownloadingModel = false;
          this.closeProgressStream();
        } else if (status.download_progress) {
          console.log('[TranscriptionComponent] Model is downloading, subscribing to progress...');
          this.streamDownloadProgress(modelName);
        } else {
          console.log('[TranscriptionComponent] Model not cached, will download on transcription');
          this.isDownloadingModel = false;
        }
      },
      error: (err) => {
        console.error('[TranscriptionComponent] Error checking model status:', err);
      }
    });
  }

  /**
   * Stream download progress using Server-Sent Events (SSE)
   */
  streamDownloadProgress(modelName: string): void {
    // Close any existing stream
    this.closeProgressStream();

    const url = this.apiService.getModelProgressUrl(modelName);
    console.log('[TranscriptionComponent] Subscribing to SSE:', url);

    this.progressEventSource = new EventSource(url);
    this.isDownloadingModel = true;
    this.downloadProgress = 0;

    this.progressEventSource.onmessage = (event) => {
      this.ngZone.run(() => {
        try {
          const data = JSON.parse(event.data);
          console.log('[TranscriptionComponent] Progress update:', data);

          if (data.status === 'done' || data.status === 'completed' || data.status === 'cached') {
            this.isDownloadingModel = false;
            this.downloadProgress = 100;
            this.closeProgressStream();
          } else if (data.status === 'error') {
            this.isDownloadingModel = false;
            this.closeProgressStream();
          } else {
            this.downloadProgress = data.progress || 0;
            this.downloadStatus = data.status || '';
          }
        } catch (e) {
          console.error('[TranscriptionComponent] Error parsing SSE data:', e);
        }
      });
    };

    this.progressEventSource.onerror = (error) => {
      console.error('[TranscriptionComponent] SSE error:', error);
      this.ngZone.run(() => {
        this.isDownloadingModel = false;
        this.closeProgressStream();
      });
    };
  }

  /**
   * Close SSE progress stream
   */
  closeProgressStream(): void {
    if (this.progressEventSource) {
      this.progressEventSource.close();
      this.progressEventSource = null;
    }
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
    console.log('[TranscriptionComponent] submitRetranscription - Starting with model:', this.selectedModel);

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

    console.log('[TranscriptionComponent] Calling retranscribeAudio for audio file:', this.activeTranscription.audio_file_id);

    this.transcriptionService.retranscribeAudio(
      this.activeTranscription.audio_file_id,
      this.selectedModel,
      this.activeTranscription.language || undefined,
      this.enableLlmEnhancement
    ).pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (newTranscription) => {
        console.log('[TranscriptionComponent] Re-transcription created:', newTranscription.id, newTranscription.model);

        // Reload all transcriptions and switch to the new one after loading completes
        // This ensures proper sorting and that we're switching to the correct reference
        this.loadAllTranscriptions(this.activeTranscription!.audio_file_id, newTranscription.id);

        // Close dialog
        this.closeRetranscribeDialog();

        this.popupService.success(
          `Transcription with model "${this.selectedModel}" started successfully!`
        ).pipe(takeUntil(this.destroy$)).subscribe();
      },
      error: (err) => {
        console.error('[TranscriptionComponent] Re-transcription failed:', err);

        // Extract error message from various possible formats
        let errorMessage = 'Failed to start re-transcription';
        if (err.error) {
          if (typeof err.error === 'string') {
            errorMessage = err.error;
          } else if (err.error.detail) {
            errorMessage = typeof err.error.detail === 'string'
              ? err.error.detail
              : JSON.stringify(err.error.detail);
          } else if (err.error.message) {
            errorMessage = err.error.message;
          }
        } else if (err.message) {
          errorMessage = err.message;
        } else if (err.statusText) {
          errorMessage = err.statusText;
        }

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

  /**
   * Format processing time for display
   */
  formatProcessingTime(seconds: number): string {
    return `${seconds.toFixed(2)}s`;
  }

  /**
   * Check if the active transcription can be enhanced with LLM
   */
  canEnhance(): boolean {
    if (!this.activeTranscription) {
      return false;
    }

    return (
      this.activeTranscription.enable_llm_enhancement &&
      this.activeTranscription.status === TranscriptionStatus.COMPLETED &&
      this.activeTranscription.text !== null &&
      this.activeTranscription.text.trim() !== '' &&
      this.activeTranscription.text !== '(No speech detected)' &&
      (this.activeTranscription.llm_enhancement_status === null ||
       this.activeTranscription.llm_enhancement_status === 'failed')
    );
  }

  /**
   * Enhance the active transcription with LLM
   */
  enhanceTranscription(): void {
    if (!this.activeTranscription || !this.canEnhance()) {
      return;
    }

    this.isEnhancing = true;
    this.error = null;

    this.transcriptionService.enhanceTranscription(this.activeTranscription.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (enhancedTranscription) => {
          console.log('[TranscriptionComponent] Enhancement completed:', enhancedTranscription);
          this.isEnhancing = false;

          // Update the active transcription and reload all transcriptions
          this.activeTranscription = enhancedTranscription;
          if (enhancedTranscription.audio_file_id) {
            this.loadAllTranscriptions(enhancedTranscription.audio_file_id);
          }

          this.popupService.success('Transcription enhanced successfully!')
            .pipe(takeUntil(this.destroy$))
            .subscribe();
        },
        error: (err) => {
          console.error('[TranscriptionComponent] Enhancement failed:', err);
          this.isEnhancing = false;

          let errorMessage = 'Failed to enhance transcription';
          if (err.error?.detail) {
            errorMessage = typeof err.error.detail === 'string'
              ? err.error.detail
              : JSON.stringify(err.error.detail);
          }

          this.error = errorMessage;
          this.popupService.error(errorMessage)
            .pipe(takeUntil(this.destroy$))
            .subscribe();
        }
      });
  }
}
