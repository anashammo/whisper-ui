import { Component, OnInit, OnDestroy, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { TranscriptionService } from '../../core/services/transcription.service';
import { ApiService } from '../../core/services/api.service';

/**
 * Upload component with drag & drop and audio recording functionality
 */
@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
export class UploadComponent implements OnInit, OnDestroy {
  selectedFile: File | null = null;
  selectedLanguage: string = '';
  selectedModel: string = 'base';
  enableLlmEnhancement: boolean = false;
  isDragging: boolean = false;
  isUploading: boolean = false;
  error: string | null = null;
  selectedFileUrl: string | null = null;
  isPlayingFile: boolean = false;
  currentAudio: HTMLAudioElement | null = null;

  // Model download progress
  isDownloadingModel: boolean = false;
  downloadProgress: number = 0;
  downloadStatus: string = '';
  progressEventSource: EventSource | null = null;

  // Mode tracking
  mode: 'upload' | 'record' = 'upload';

  // Audio recording properties
  isRecording: boolean = false;
  isPaused: boolean = false;
  recordedAudioUrl: string | null = null;
  recordingDuration: number = 0;
  mediaRecorder: MediaRecorder | null = null;
  audioChunks: Blob[] = [];
  recordingTimer: any = null;
  audioStream: MediaStream | null = null;

  // Supported languages
  languages = [
    { code: '', name: 'Auto-detect' },
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'ru', name: 'Russian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ar', name: 'Arabic' },
    { code: 'hi', name: 'Hindi' }
  ];

  // Whisper models - unified descriptions matching backend configuration
  models = [
    { code: 'tiny', name: 'Tiny - Fastest model with acceptable accuracy', size: '~75MB' },
    { code: 'base', name: 'Base - Recommended for general use (best balance)', size: '~150MB' },
    { code: 'small', name: 'Small - Balanced performance with better accuracy', size: '~500MB' },
    { code: 'medium', name: 'Medium - High accuracy for important transcriptions', size: '~1.5GB' },
    { code: 'large', name: 'Large - Best accuracy for critical transcriptions', size: '~3GB' },
    { code: 'turbo', name: 'Turbo - Optimized for speed and accuracy', size: '~3GB' }
  ];

  constructor(
    private transcriptionService: TranscriptionService,
    private router: Router,
    private ngZone: NgZone,
    private apiService: ApiService
  ) {}

  ngOnInit(): void {
    // Check initial model status
    this.checkModelStatus(this.selectedModel);
  }

  /**
   * Handle file selection from input
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  /**
   * Handle drag over event
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  /**
   * Handle drag leave event
   */
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  /**
   * Handle file drop
   */
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  /**
   * Handle file validation and selection
   */
  private handleFile(file: File): void {
    this.error = null;

    // Validate file type
    const supportedTypes = [
      'audio/mpeg',
      'audio/mp3',
      'audio/wav',
      'audio/x-wav',
      'audio/mp4',
      'audio/x-m4a',
      'audio/m4a',
      'audio/ogg',
      'audio/flac',
      'audio/webm'
    ];

    if (!supportedTypes.includes(file.type)) {
      this.error = 'Unsupported file type. Please upload an audio file (MP3, WAV, M4A, FLAC, OGG, WEBM).';
      return;
    }

    // Validate file size (25MB max)
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      this.error = 'File size exceeds 25MB limit.';
      return;
    }

    this.selectedFile = file;

    // Create object URL for playback
    this.selectedFileUrl = URL.createObjectURL(file);
  }

  /**
   * Called when user selects a different model
   */
  onModelChange(): void {
    console.log('Model changed to:', this.selectedModel);
    this.checkModelStatus(this.selectedModel);
  }

  /**
   * Check if model is cached and start progress tracking if downloading
   */
  checkModelStatus(modelName: string): void {
    this.apiService.getModelStatus(modelName).subscribe({
      next: (status) => {
        console.log('Model status:', status);

        if (status.is_cached || status.is_loaded) {
          // Model is already cached, no download needed
          this.isDownloadingModel = false;
          this.downloadProgress = 100;
          this.downloadStatus = 'cached';
        } else {
          // Model will need to be downloaded
          this.downloadStatus = 'needs_download';
          this.downloadProgress = 0;
        }
      },
      error: (error) => {
        console.error('Error checking model status:', error);
      }
    });
  }

  /**
   * Subscribe to model download progress via SSE
   */
  subscribeToModelProgress(modelName: string): void {
    // Close any existing connection
    this.closeProgressStream();

    const url = this.apiService.getModelProgressUrl(modelName);
    console.log('Subscribing to SSE:', url);

    this.progressEventSource = new EventSource(url);
    this.isDownloadingModel = true;
    this.downloadProgress = 0;

    this.progressEventSource.onmessage = (event) => {
      this.ngZone.run(() => {
        try {
          const data = JSON.parse(event.data);
          console.log('Progress update:', data);

          this.downloadStatus = data.status;
          this.downloadProgress = data.progress || 0;

          if (data.status === 'completed' || data.status === 'cached' || data.status === 'done') {
            this.isDownloadingModel = false;
            this.downloadProgress = 100;
            this.closeProgressStream();
          } else if (data.status === 'error') {
            this.isDownloadingModel = false;
            this.error = 'Model download failed: ' + (data.error_message || 'Unknown error');
            this.closeProgressStream();
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      });
    };

    this.progressEventSource.onerror = (error) => {
      console.error('SSE error:', error);
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
   * Upload and transcribe the selected file
   */
  uploadFile(): void {
    if (!this.selectedFile) {
      return;
    }

    // Start model progress tracking if model is not cached
    if (this.downloadStatus === 'needs_download') {
      this.subscribeToModelProgress(this.selectedModel);
    }

    this.isUploading = true;
    this.error = null;

    const language = this.selectedLanguage || undefined;
    const model = this.selectedModel || 'base';

    this.transcriptionService.uploadAudio(this.selectedFile, language, model, this.enableLlmEnhancement).subscribe({
      next: (transcription) => {
        this.isUploading = false;
        this.isDownloadingModel = false;
        this.closeProgressStream();
        // Navigate to transcription detail
        this.router.navigate(['/transcription', transcription.id]);
      },
      error: (error) => {
        this.isUploading = false;
        this.isDownloadingModel = false;
        this.closeProgressStream();
        this.error = error.error?.detail || 'Upload failed. Please try again.';
      }
    });
  }

  /**
   * Clear selected file
   */
  clearFile(): void {
    if (this.selectedFileUrl) {
      URL.revokeObjectURL(this.selectedFileUrl);
      this.selectedFileUrl = null;
    }
    this.selectedFile = null;
    this.error = null;
  }

  /**
   * Play uploaded file
   */
  playFile(): void {
    // If already playing, do nothing (button will show stop instead)
    if (this.isPlayingFile) {
      return;
    }

    // Stop any currently playing audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
    }

    if (!this.selectedFileUrl) {
      console.error('No audio URL available');
      this.error = 'No audio file loaded';
      return;
    }

    console.log('Playing uploaded file from URL:', this.selectedFileUrl);
    console.log('File type:', this.selectedFile?.type);

    this.currentAudio = new Audio(this.selectedFileUrl);
    this.isPlayingFile = true;
    this.error = null;

    this.currentAudio.addEventListener('loadeddata', () => {
      console.log('Audio loaded successfully, duration:', this.currentAudio?.duration);
    });

    this.currentAudio.addEventListener('error', (e: any) => {
      console.error('Audio playback error:', e);
      console.error('Error code:', this.currentAudio?.error?.code);
      console.error('Error message:', this.currentAudio?.error?.message);
      this.ngZone.run(() => {
        this.isPlayingFile = false;
        this.error = 'Failed to play audio file. Format may not be supported by browser.';
      });
    });

    this.currentAudio.addEventListener('ended', () => {
      console.log('Audio playback ended');
      this.ngZone.run(() => {
        this.isPlayingFile = false;
      });
    });

    this.currentAudio.addEventListener('pause', () => {
      console.log('Audio paused');
      this.ngZone.run(() => {
        this.isPlayingFile = false;
      });
    });

    this.currentAudio.play().then(() => {
      console.log('Audio playback started successfully');
    }).catch(err => {
      console.error('Play failed:', err);
      this.ngZone.run(() => {
        this.isPlayingFile = false;
        this.error = 'Failed to play audio: ' + err.message;
      });
    });
  }

  /**
   * Stop audio playback
   */
  stopFile(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.isPlayingFile = false;
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Switch to upload mode
   */
  switchToUploadMode(): void {
    this.mode = 'upload';
    this.cancelRecording();
  }

  /**
   * Switch to recording mode
   */
  switchToRecordMode(): void {
    this.mode = 'record';
    this.selectedFile = null;
    this.error = null;
  }

  /**
   * Start audio recording from microphone
   */
  async startRecording(): Promise<void> {
    try {
      this.error = null;
      this.audioChunks = [];
      this.recordingDuration = 0;
      this.mode = 'record';

      // Check if browser supports getUserMedia
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.error = 'Your browser does not support audio recording. Please use a modern browser like Chrome, Firefox, or Edge.';
        return;
      }

      // Request microphone access
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });

      console.log('Audio stream obtained:', this.audioStream);
      console.log('Audio tracks:', this.audioStream.getAudioTracks());

      // Create media recorder
      this.mediaRecorder = new MediaRecorder(this.audioStream);
      console.log('MediaRecorder created. MIME type:', this.mediaRecorder.mimeType);
      console.log('MediaRecorder state:', this.mediaRecorder.state);

      // Handle data available event
      this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      // Handle stop event
      this.mediaRecorder.onstop = () => {
        // Run inside Angular zone to trigger change detection
        this.ngZone.run(() => {
          console.log('Recording stopped. Audio chunks:', this.audioChunks.length);
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
          console.log('Audio blob size:', audioBlob.size, 'bytes');

          if (audioBlob.size === 0) {
            this.error = 'Recording failed: No audio data captured. Please check your microphone permissions and try again.';
            return;
          }

          this.recordedAudioUrl = URL.createObjectURL(audioBlob);
          console.log('Created audio URL:', this.recordedAudioUrl);

          // Convert blob to file
          const file = new File([audioBlob], `recording-${Date.now()}.webm`, {
            type: 'audio/webm'
          });
          this.selectedFile = file;
          console.log('Created file:', file.name, 'size:', file.size);
        });
      };

      // Start recording with timeslice to ensure data collection
      this.mediaRecorder.start(1000); // Collect data every second
      this.isRecording = true;

      // Start timer
      this.recordingTimer = setInterval(() => {
        this.recordingDuration++;

        // Auto-stop at 30 seconds
        if (this.recordingDuration >= 30) {
          this.stopRecording();
        }
      }, 1000);

    } catch (error: any) {
      console.error('Error starting recording:', error);

      // Handle specific error types
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        this.error = 'Microphone access denied. Please grant permission in your browser settings and try again.';
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        this.error = 'No microphone found. Please connect a microphone and try again.';
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        this.error = 'Microphone is being used by another application. Please close other apps and try again.';
      } else {
        this.error = 'Failed to start recording: ' + (error.message || 'Unknown error');
      }
    }
  }

  /**
   * Stop audio recording
   */
  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;

      // Stop timer
      if (this.recordingTimer) {
        clearInterval(this.recordingTimer);
        this.recordingTimer = null;
      }

      // Stop all tracks
      if (this.audioStream) {
        this.audioStream.getTracks().forEach(track => track.stop());
      }
    }
  }

  /**
   * Cancel recording and clear state
   */
  cancelRecording(): void {
    this.stopRecording();
    this.recordedAudioUrl = null;
    this.recordingDuration = 0;
    this.audioChunks = [];
    this.selectedFile = null;
  }

  // Track recording playback state
  isPlayingRecording: boolean = false;
  recordingAudio: HTMLAudioElement | null = null;

  /**
   * Play recorded audio
   */
  playRecording(): void {
    // If already playing, do nothing (button will show stop instead)
    if (this.isPlayingRecording) {
      return;
    }

    // Stop any currently playing recording
    if (this.recordingAudio) {
      this.recordingAudio.pause();
      this.recordingAudio.currentTime = 0;
    }

    if (!this.recordedAudioUrl) {
      console.error('No recorded audio URL available');
      return;
    }

    console.log('Playing audio from URL:', this.recordedAudioUrl);
    this.recordingAudio = new Audio(this.recordedAudioUrl);
    this.isPlayingRecording = true;

    this.recordingAudio.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      this.ngZone.run(() => {
        this.isPlayingRecording = false;
        this.error = 'Failed to play recorded audio. The recording may be corrupted.';
      });
    });

    this.recordingAudio.addEventListener('ended', () => {
      this.ngZone.run(() => {
        this.isPlayingRecording = false;
      });
    });

    this.recordingAudio.addEventListener('pause', () => {
      this.ngZone.run(() => {
        this.isPlayingRecording = false;
      });
    });

    this.recordingAudio.play().then(() => {
      console.log('Audio playback started');
    }).catch(err => {
      console.error('Play failed:', err);
      this.ngZone.run(() => {
        this.isPlayingRecording = false;
        this.error = 'Failed to play audio: ' + err.message;
      });
    });
  }

  /**
   * Stop recorded audio playback
   */
  stopRecordingPlayback(): void {
    if (this.recordingAudio) {
      this.recordingAudio.pause();
      this.recordingAudio.currentTime = 0;
      this.recordingAudio = null;
    }
    this.isPlayingRecording = false;
  }

  /**
   * Format recording duration for display
   */
  formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * Component cleanup
   */
  ngOnDestroy(): void {
    // Stop and clean up audio playback
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }

    // Stop and clean up recording playback
    if (this.recordingAudio) {
      this.recordingAudio.pause();
      this.recordingAudio = null;
    }

    // Clean up recording resources
    if (this.isRecording) {
      this.stopRecording();
    }

    if (this.recordedAudioUrl) {
      URL.revokeObjectURL(this.recordedAudioUrl);
    }

    if (this.selectedFileUrl) {
      URL.revokeObjectURL(this.selectedFileUrl);
    }

    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
    }

    // Close SSE progress stream
    this.closeProgressStream();
  }
}
