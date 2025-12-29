import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranscriptionService } from '../../core/services/transcription.service';
import { Transcription } from '../../core/models/transcription.model';
import { AudioFileWithTranscriptions } from '../../core/models/audio-file.model';
import { PopupService } from '../../shared/services/popup.service';

/**
 * History list component with grouped audio file view
 */
@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit, OnDestroy {
  audioFilesWithTranscriptions: AudioFileWithTranscriptions[] = [];
  isLoading: boolean = false;
  error: string | null = null;
  private destroy$ = new Subject<void>();

  // Audio file expansion state
  expandedAudioFileIds: Set<string> = new Set<string>();

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

    // Subscribe to transcriptions list and group by audio file
    this.transcriptionService
      .getTranscriptions()
      .pipe(takeUntil(this.destroy$))
      .subscribe((transcriptions) => {
        this.audioFilesWithTranscriptions = this.groupTranscriptionsByAudioFile(transcriptions);
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
   * Group transcriptions by audio file
   */
  private groupTranscriptionsByAudioFile(transcriptions: Transcription[]): AudioFileWithTranscriptions[] {
    const groupedMap = new Map<string, Transcription[]>();

    // Group transcriptions by audio_file_id
    transcriptions.forEach(trans => {
      const audioFileId = trans.audio_file_id;
      if (!groupedMap.has(audioFileId)) {
        groupedMap.set(audioFileId, []);
      }
      groupedMap.get(audioFileId)!.push(trans);
    });

    // Convert map to array of AudioFileWithTranscriptions
    const result: AudioFileWithTranscriptions[] = [];
    groupedMap.forEach((transcriptionList, audioFileId) => {
      // Sort transcriptions by created_at DESC (newest first)
      transcriptionList.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      // Use the first (most recent) transcription to get audio file metadata
      const firstTrans = transcriptionList[0];

      result.push({
        audio_file: {
          id: audioFileId,
          original_filename: firstTrans.audio_file_original_filename || `Audio File ${audioFileId.substring(0, 8)}`,
          file_size_bytes: 0, // Placeholder
          mime_type: '', // Placeholder
          duration_seconds: firstTrans.duration_seconds,
          uploaded_at: firstTrans.created_at
        },
        transcriptions: transcriptionList,
        transcription_count: transcriptionList.length
      });
    });

    // Sort audio files by most recent transcription (newest first)
    result.sort((a, b) =>
      new Date(b.audio_file.uploaded_at).getTime() - new Date(a.audio_file.uploaded_at).getTime()
    );

    return result;
  }

  /**
   * Toggle expansion state for an audio file
   */
  toggleExpanded(audioFileId: string, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }

    if (this.expandedAudioFileIds.has(audioFileId)) {
      this.expandedAudioFileIds.delete(audioFileId);
    } else {
      this.expandedAudioFileIds.add(audioFileId);
    }
  }

  /**
   * Check if an audio file is expanded
   */
  isExpanded(audioFileId: string): boolean {
    return this.expandedAudioFileIds.has(audioFileId);
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
  /**
   * Delete an audio file and all associated transcriptions
   */
  deleteAudioFile(audioFileId: string, transcriptionCount: number, event: Event): void {
    event.stopPropagation(); // Prevent expand/collapse toggle

    console.log('[HistoryComponent] deleteAudioFile called with ID:', audioFileId);
    console.log('[HistoryComponent] Transcription count:', transcriptionCount);

    const message = transcriptionCount === 1
      ? 'Are you sure you want to delete this audio file and its transcription? This action cannot be undone.'
      : `Are you sure you want to delete this audio file and all ${transcriptionCount} transcriptions? This action cannot be undone.`;

    this.popupService.confirm(
      'Delete Audio File',
      message,
      'Delete All',
      'Cancel'
    ).pipe(takeUntil(this.destroy$))
    .subscribe((confirmed) => {
      if (!confirmed) {
        console.log('[HistoryComponent] Delete cancelled by user');
        return;
      }

      console.log('[HistoryComponent] Delete confirmed, calling API with ID:', audioFileId);
      this.transcriptionService.deleteAudioFile(audioFileId).subscribe({
        next: () => {
          console.log(`[HistoryComponent] ✅ Audio file ${audioFileId} and all transcriptions deleted successfully`);
          // Remove from local array
          this.audioFilesWithTranscriptions = this.audioFilesWithTranscriptions.filter(
            af => af.audio_file.id !== audioFileId
          );
          // Close if was expanded
          this.expandedAudioFileIds.delete(audioFileId);
        },
        error: (error) => {
          console.error('[HistoryComponent] ❌ Delete failed with error:', error);
          console.error('[HistoryComponent] Error status:', error.status);
          console.error('[HistoryComponent] Error detail:', error.error?.detail);
          console.error('[HistoryComponent] Full error object:', JSON.stringify(error, null, 2));
          this.error = 'Failed to delete audio file: ' + (error.error?.detail || error.message || 'Unknown error');
        }
      });
    });
  }

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
