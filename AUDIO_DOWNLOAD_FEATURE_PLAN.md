# Audio Download Feature - Implementation Plan

**Feature**: Enable users to download audio files from Transcription History and Transcription Details views

**Date**: 2024-12-30

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Requirements](#requirements)
3. [Impact Analysis](#impact-analysis)
4. [Implementation Breakdown](#implementation-breakdown)
5. [Testing Plan](#testing-plan)
6. [Documentation Updates](#documentation-updates)
7. [Rollback Plan](#rollback-plan)

---

## Executive Summary

### Objective
Add download functionality for audio files in two locations:
- **Transcription History View**: Icon-only download button next to play button
- **Transcription Details View**: Download button with icon + text next to play button

### Key Decisions
- **Filename**: Use original filename from upload (e.g., "my-recording.mp3")
- **Behavior**: Immediate browser download trigger
- **API**: Reuse existing `/transcriptions/{transcription_id}/audio` endpoint with download parameter
- **Availability**: Download available for all transcriptions regardless of status

### Estimated Complexity
- **Backend**: Low (1 file, ~10 lines of code)
- **Frontend**: Low-Medium (4 files, ~100 lines total)
- **Testing**: Medium (both views, multiple scenarios)
- **Documentation**: Low (2-3 files)

---

## Requirements

### Functional Requirements
1. ✅ Add download button in Transcription History view (icon only: "⬇️")
2. ✅ Add download button in Transcription Details view (icon + text: "⬇️ Download")
3. ✅ Download button positioned immediately after play button in both views
4. ✅ Clicking download button triggers immediate browser download
5. ✅ Downloaded file uses original filename from upload
6. ✅ Download available for all transcriptions (pending, processing, completed, failed)

### Non-Functional Requirements
1. ✅ Consistent styling with existing buttons (`.btn-icon` pattern)
2. ✅ No breaking of existing play/delete functionality
3. ✅ Clean architecture maintained (Clean Architecture layers respected)
4. ✅ Error handling for missing/deleted audio files
5. ✅ Accessible UI (title tooltips on buttons)

---

## Impact Analysis

### Layer 1: Database
**Impact**: ✅ **NONE**
- No schema changes required
- Audio file metadata (`original_filename`, `file_path`) already exists
- No migrations needed

### Layer 2: Domain Layer
**Impact**: ✅ **NONE**
- No changes to entities (`AudioFile`, `Transcription`)
- No changes to repositories (interfaces or implementations)
- No changes to domain services

### Layer 3: Application Layer
**Impact**: ✅ **NONE**
- No new use cases required
- Existing use cases remain unchanged

### Layer 4: Infrastructure Layer
**Impact**: ⚠️ **MINIMAL**
- **File**: `src/presentation/api/routers/transcription_router.py`
- **Change**: Add query parameter `download` to existing audio endpoint
- **Lines Modified**: ~10 lines
- **Risk**: Low (backward compatible change)

### Layer 5: Presentation Layer (Backend)
**Impact**: ⚠️ **LOW**
- **File Modified**: `src/presentation/api/routers/transcription_router.py`
- **Change**: Modify `/transcriptions/{transcription_id}/audio` endpoint
- **Details**: Add `Content-Disposition: attachment` header when `download=true` query param present

### Layer 6: Presentation Layer (Frontend)

#### **History Component**
**Impact**: ⚠️ **MEDIUM**
- **Files Modified**:
  - `src/presentation/frontend/src/app/features/history/history.component.html` (~5 lines)
  - `src/presentation/frontend/src/app/features/history/history.component.ts` (~15 lines)
  - `src/presentation/frontend/src/app/features/history/history.component.css` (~10 lines)
- **Changes**:
  - Add download button in template
  - Add `downloadAudio(event, transcriptionId)` method
  - Add `.btn-download-small` CSS styling

#### **Transcription Details Component**
**Impact**: ⚠️ **MEDIUM**
- **Files Modified**:
  - `src/presentation/frontend/src/app/features/transcription/transcription.component.html` (~5 lines)
  - `src/presentation/frontend/src/app/features/transcription/transcription.component.ts` (~15 lines)
  - `src/presentation/frontend/src/app/features/transcription/transcription.component.css` (~10 lines)
- **Changes**:
  - Add download button in template
  - Add `downloadAudio()` method
  - Add `.btn-download` CSS styling

#### **Services**
**Impact**: ⚠️ **LOW**
- **Files Modified**:
  - `src/presentation/frontend/src/app/core/services/api.service.ts` (~5 lines)
  - `src/presentation/frontend/src/app/core/services/transcription.service.ts` (~5 lines)
- **Changes**:
  - Add `getAudioDownloadUrl(id: string)` method to both services

### Layer 7: Scripts
**Impact**: ✅ **NONE**
- No changes to server management scripts
- No changes to database scripts
- No changes to model download scripts

### Layer 8: Documentation
**Impact**: ⚠️ **LOW**
- **Files Modified**:
  - `CLAUDE.md` - Add download feature to API endpoints section
  - `README.md` (if exists) - Add download to features list
  - This plan document becomes part of documentation

---

## Implementation Breakdown

### Phase 1: Backend Changes (Estimated: 10 minutes)

#### Step 1.1: Modify Audio Endpoint
**File**: `src/presentation/api/routers/transcription_router.py`
**Location**: Lines 215-273 (existing `get_audio_file` endpoint)

**Current Code**:
```python
@router.get(
    "/transcriptions/{transcription_id}/audio",
    summary="Get audio file",
    description="Download the original audio file for a transcription."
)
async def get_audio_file(
    transcription_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the audio file for a specific transcription.

    Args:
        transcription_id: ID of the transcription

    Returns:
        FileResponse with audio file
    """
    try:
        # Get transcription
        transcription_repo = SQLiteTranscriptionRepository(db)
        transcription = await transcription_repo.get_by_id(transcription_id)

        if not transcription:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription {transcription_id} not found"
            )

        # Get audio file
        audio_file_repo = SQLiteAudioFileRepository(db)
        audio_file = await audio_file_repo.get_by_id(transcription.audio_file_id)

        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found for transcription {transcription_id}"
            )

        # Check if file exists on disk
        if not os.path.exists(audio_file.file_path):
            raise HTTPException(
                status_code=404,
                detail="Audio file not found on server"
            )

        # Return file response
        return FileResponse(
            path=audio_file.file_path,
            media_type=audio_file.mime_type or "application/octet-stream",
            filename=audio_file.original_filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audio file: {str(e)}"
        )
```

**Modified Code** (add `download` query parameter):
```python
@router.get(
    "/transcriptions/{transcription_id}/audio",
    summary="Get audio file",
    description="Stream or download the original audio file for a transcription."
)
async def get_audio_file(
    transcription_id: str,
    download: bool = Query(
        False,
        description="If true, sets Content-Disposition to attachment for download"
    ),
    db: Session = Depends(get_db)
):
    """
    Get the audio file for a specific transcription.

    Args:
        transcription_id: ID of the transcription
        download: If True, force download instead of inline playback

    Returns:
        FileResponse with audio file (streaming or download)
    """
    try:
        # Get transcription
        transcription_repo = SQLiteTranscriptionRepository(db)
        transcription = await transcription_repo.get_by_id(transcription_id)

        if not transcription:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription {transcription_id} not found"
            )

        # Get audio file
        audio_file_repo = SQLiteAudioFileRepository(db)
        audio_file = await audio_file_repo.get_by_id(transcription.audio_file_id)

        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found for transcription {transcription_id}"
            )

        # Check if file exists on disk
        if not os.path.exists(audio_file.file_path):
            raise HTTPException(
                status_code=404,
                detail="Audio file not found on server"
            )

        # Determine Content-Disposition header
        # If download=true, use "attachment" to force download
        # Otherwise, use "inline" for browser playback
        headers = {}
        if download:
            headers["Content-Disposition"] = f'attachment; filename="{audio_file.original_filename}"'

        # Return file response
        return FileResponse(
            path=audio_file.file_path,
            media_type=audio_file.mime_type or "application/octet-stream",
            filename=audio_file.original_filename,
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audio file: {str(e)}"
        )
```

**Changes Summary**:
- ✅ Added `download: bool` query parameter (default: `False`)
- ✅ Added `headers` dict to conditionally set `Content-Disposition: attachment`
- ✅ Updated docstring to reflect streaming vs download behavior
- ✅ Updated endpoint description
- ✅ Backward compatible (existing play functionality unchanged)

**Testing Commands**:
```bash
# Test streaming (existing behavior)
curl http://localhost:8001/api/v1/transcriptions/{id}/audio

# Test download (new behavior)
curl http://localhost:8001/api/v1/transcriptions/{id}/audio?download=true -O
```

---

### Phase 2: Frontend Service Changes (Estimated: 10 minutes)

#### Step 2.1: Update API Service
**File**: `src/presentation/frontend/src/app/core/services/api.service.ts`
**Location**: After `getAudioUrl()` method (around line 143)

**Add New Method**:
```typescript
/**
 * Get audio file download URL with download parameter
 * This triggers browser download instead of inline playback
 */
getAudioDownloadUrl(id: string): string {
  return `${this.apiUrl}/transcriptions/${id}/audio?download=true`;
}
```

**Changes Summary**:
- ✅ Added `getAudioDownloadUrl(id)` method
- ✅ Returns URL with `?download=true` query parameter
- ✅ Separate from `getAudioUrl()` to maintain clear separation of concerns

#### Step 2.2: Update Transcription Service
**File**: `src/presentation/frontend/src/app/core/services/transcription.service.ts`
**Location**: After `getAudioUrl()` method (around line 218)

**Add New Method**:
```typescript
/**
 * Get audio file download URL
 * Triggers browser download instead of inline playback
 */
getAudioDownloadUrl(id: string): string {
  return this.apiService.getAudioDownloadUrl(id);
}
```

**Changes Summary**:
- ✅ Added `getAudioDownloadUrl(id)` method
- ✅ Delegates to API service (following existing pattern)

---

### Phase 3: Frontend History Component (Estimated: 20 minutes)

#### Step 3.1: Update History Template
**File**: `src/presentation/frontend/src/app/features/history/history.component.html`
**Location**: Lines 96-102 (after play button)

**Current Code** (lines 96-102):
```html
<button
  class="btn-icon btn-play-small"
  (click)="isPlaying(transcription.id) ? stopAudio($event) : playAudio($event, transcription.id)"
  [title]="isPlaying(transcription.id) ? 'Stop audio' : 'Play audio'"
>
  {{ isPlaying(transcription.id) ? '⏹️' : '▶️' }}
</button>
```

**Modified Code** (add download button immediately after):
```html
<!-- Play/Stop Button -->
<button
  class="btn-icon btn-play-small"
  (click)="isPlaying(transcription.id) ? stopAudio($event) : playAudio($event, transcription.id)"
  [title]="isPlaying(transcription.id) ? 'Stop audio' : 'Play audio'"
>
  {{ isPlaying(transcription.id) ? '⏹️' : '▶️' }}
</button>

<!-- Download Button -->
<button
  class="btn-icon btn-download-small"
  (click)="downloadAudio($event, transcription.id)"
  title="Download audio file"
>
  ⬇️
</button>
```

**Changes Summary**:
- ✅ Added download button with icon "⬇️"
- ✅ Icon-only (no text) as per requirements
- ✅ Positioned immediately after play button
- ✅ Uses `btn-icon btn-download-small` CSS classes
- ✅ Calls `downloadAudio($event, transcription.id)` on click
- ✅ Tooltip: "Download audio file"

#### Step 3.2: Update History Component TypeScript
**File**: `src/presentation/frontend/src/app/features/history/history.component.ts`
**Location**: After `stopAudio()` method (around line 262)

**Add New Method**:
```typescript
/**
 * Download audio file for a transcription
 * Creates a temporary anchor element to trigger browser download
 */
downloadAudio(event: Event, transcriptionId: string): void {
  // Prevent event bubbling (don't trigger row click)
  event.stopPropagation();

  try {
    // Get download URL with download=true parameter
    const downloadUrl = this.transcriptionService.getAudioDownloadUrl(transcriptionId);

    // Create temporary anchor element
    const anchor = document.createElement('a');
    anchor.href = downloadUrl;
    anchor.style.display = 'none';

    // Append to body, click, then remove
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);

    console.log(`Initiated download for transcription ${transcriptionId}`);
  } catch (err) {
    console.error('Download failed:', err);
    this.error = 'Failed to download audio file';
  }
}
```

**Changes Summary**:
- ✅ Added `downloadAudio(event, transcriptionId)` method
- ✅ Prevents event bubbling with `stopPropagation()`
- ✅ Creates temporary `<a>` element for download
- ✅ Uses service to get download URL
- ✅ Error handling with console logging and error display
- ✅ Follows existing pattern from `playAudio()` and `stopAudio()`

#### Step 3.3: Update History Component CSS
**File**: `src/presentation/frontend/src/app/features/history/history.component.css`
**Location**: After `.btn-play-small` (around line 180)

**Add New Styles**:
```css
/* Download button (small, icon-only for history cards) */
.btn-download-small {
  background: none;
  border: 1px solid #4299e1;
  color: #4299e1;
  padding: 0.25rem 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  margin-left: 0.25rem;
}

.btn-download-small:hover {
  background-color: #4299e1;
  color: white;
  transform: translateY(-1px);
}

.btn-download-small:active {
  transform: translateY(0);
}
```

**Changes Summary**:
- ✅ Added `.btn-download-small` styling
- ✅ Blue color scheme (`#4299e1`) to match primary color
- ✅ Hover effect (background fill + lift)
- ✅ Active state (press down)
- ✅ Consistent with `.btn-play-small` sizing
- ✅ `margin-left: 0.25rem` for spacing from play button

---

### Phase 4: Frontend Transcription Details Component (Estimated: 20 minutes)

#### Step 4.1: Update Transcription Details Template
**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.html`
**Location**: Lines 140-146 (after play button in "Transcription Result" section)

**Current Code** (lines 140-146):
```html
<button
  class="btn btn-icon"
  (click)="isPlayingAudio ? stopAudio() : playAudio()"
  [title]="isPlayingAudio ? 'Stop audio' : 'Play original audio'"
>
  {{ isPlayingAudio ? '⏹️' : '▶️' }} {{ isPlayingAudio ? 'Stop' : 'Play' }} Audio
</button>
```

**Modified Code** (add download button immediately after):
```html
<!-- Play/Stop Audio Button -->
<button
  class="btn btn-icon"
  (click)="isPlayingAudio ? stopAudio() : playAudio()"
  [title]="isPlayingAudio ? 'Stop audio' : 'Play original audio'"
>
  {{ isPlayingAudio ? '⏹️' : '▶️' }} {{ isPlayingAudio ? 'Stop' : 'Play' }} Audio
</button>

<!-- Download Audio Button -->
<button
  class="btn btn-icon btn-download"
  (click)="downloadAudio()"
  title="Download original audio file"
>
  ⬇️ Download
</button>
```

**Changes Summary**:
- ✅ Added download button with icon + text ("⬇️ Download")
- ✅ Positioned immediately after play button
- ✅ Uses `btn btn-icon btn-download` CSS classes
- ✅ Calls `downloadAudio()` on click (no parameters needed, uses current transcription)
- ✅ Tooltip: "Download original audio file"

#### Step 4.2: Update Transcription Details Component TypeScript
**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.ts`
**Location**: After `stopAudio()` method (around line 240)

**Add New Method**:
```typescript
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
```

**Changes Summary**:
- ✅ Added `downloadAudio()` method (no parameters, uses `this.transcription`)
- ✅ Null check for `this.transcription` before proceeding
- ✅ Creates temporary `<a>` element for download
- ✅ Uses service to get download URL
- ✅ Error handling with console logging and error display
- ✅ Follows existing pattern from `playAudio()` and `stopAudio()`

#### Step 4.3: Update Transcription Details Component CSS
**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.css`
**Location**: After existing button styles (around line 200)

**Add New Styles**:
```css
/* Download button (icon + text for details view) */
.btn-download {
  background-color: #4299e1;
  color: white;
  margin-left: 0.5rem;
}

.btn-download:hover {
  background-color: #3182ce;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-download:active {
  transform: translateY(0);
  box-shadow: none;
}
```

**Changes Summary**:
- ✅ Added `.btn-download` styling
- ✅ Blue background (`#4299e1`) for primary action
- ✅ Darker blue on hover (`#3182ce`)
- ✅ Lift effect on hover with shadow
- ✅ Active state (press down)
- ✅ `margin-left: 0.5rem` for spacing from play button
- ✅ Inherits base `.btn` styles from parent

---

### Phase 5: Testing Plan (Estimated: 30 minutes)

#### Test Suite 1: Backend API Testing

**Test 5.1: Audio Streaming (Existing Behavior)**
```bash
# Should work as before (inline playback)
curl -I http://localhost:8001/api/v1/transcriptions/{transcription_id}/audio

# Expected Response Headers:
# HTTP/1.1 200 OK
# content-type: audio/mpeg (or appropriate MIME type)
# content-length: {file_size}
# (No Content-Disposition header, defaults to inline)
```

**Test 5.2: Audio Download (New Behavior)**
```bash
# Should force download
curl -I http://localhost:8001/api/v1/transcriptions/{transcription_id}/audio?download=true

# Expected Response Headers:
# HTTP/1.1 200 OK
# content-type: audio/mpeg
# content-disposition: attachment; filename="original-filename.mp3"
# content-length: {file_size}
```

**Test 5.3: Error Handling**
```bash
# Non-existent transcription
curl -I http://localhost:8001/api/v1/transcriptions/invalid-id/audio?download=true
# Expected: 404 Not Found

# Deleted audio file
# (Manually delete audio file, then request)
# Expected: 404 Not Found with message "Audio file not found on server"
```

#### Test Suite 2: Frontend History View Testing

**Test 5.4: Download Button Visibility**
- ✅ Download button appears next to play button on all transcription cards
- ✅ Button shows only icon "⬇️" (no text)
- ✅ Tooltip "Download audio file" appears on hover
- ✅ Button styling matches design (blue border, icon-only)

**Test 5.5: Download Button Functionality**
- ✅ Click download button → browser download starts immediately
- ✅ Downloaded file has correct original filename
- ✅ Click event doesn't trigger card navigation (stopPropagation works)
- ✅ Download works while audio is playing (no interference)
- ✅ Download works for all statuses (pending, processing, completed, failed)

**Test 5.6: Error Scenarios**
- ✅ Download non-existent audio → error message displayed
- ✅ Network error → error message displayed
- ✅ Console logs error details for debugging

#### Test Suite 3: Frontend Details View Testing

**Test 5.7: Download Button Visibility**
- ✅ Download button appears next to play button in Transcription Result section
- ✅ Button shows icon + text "⬇️ Download"
- ✅ Tooltip "Download original audio file" appears on hover
- ✅ Button styling matches design (blue background, white text)

**Test 5.8: Download Button Functionality**
- ✅ Click download button → browser download starts immediately
- ✅ Downloaded file has correct original filename
- ✅ Download works while audio is playing (no interference)
- ✅ Download works when switching between transcription tabs
- ✅ Download works for all transcription statuses

**Test 5.9: Error Scenarios**
- ✅ No transcription loaded → button disabled or error handled
- ✅ Download non-existent audio → error message displayed

#### Test Suite 4: Cross-Browser Testing

**Test 5.10: Browser Compatibility**
- ✅ Chrome: Download works, filename correct
- ✅ Firefox: Download works, filename correct
- ✅ Edge: Download works, filename correct
- ✅ Safari: Download works, filename correct

#### Test Suite 5: Regression Testing

**Test 5.11: Existing Functionality**
- ✅ Play button still works in History view
- ✅ Play button still works in Details view
- ✅ Delete button still works in History view
- ✅ Card navigation still works in History view
- ✅ Tab switching still works in Details view
- ✅ LLM enhancement still works
- ✅ Re-transcription still works

---

### Phase 6: Documentation Updates (Estimated: 15 minutes)

#### Step 6.1: Update CLAUDE.md

**File**: `CLAUDE.md`
**Section**: API Design Patterns → API Endpoints

**Add to API Endpoints List** (around line 60):
```markdown
## API Endpoints

### Audio File Endpoints

**Stream or Download Audio**
- **Endpoint**: `GET /api/v1/transcriptions/{transcription_id}/audio`
- **Query Parameters**:
  - `download` (optional, boolean): If `true`, forces browser download with `Content-Disposition: attachment`
- **Returns**: Audio file as `FileResponse`
- **Behavior**:
  - `download=false` (default): Streams audio for inline playback
  - `download=true`: Triggers browser download with original filename
- **Use Cases**:
  - Inline playback: Play button in UI (no download param)
  - File download: Download button in UI (download=true)
```

**Add to Frontend Features** (around line 35):
```markdown
**UI Features**:
- Audio playback with play/stop controls in History and Details views
- **Audio download button** in both History and Details views
  - History view: Icon-only download button (⬇️) next to play button
  - Details view: Download button with icon + text (⬇️ Download)
  - Downloads original audio file with original filename
  - Available for all transcription statuses
```

#### Step 6.2: Update README.md (if exists)

**File**: `README.md`
**Section**: Features

**Add to Features List**:
```markdown
## Features

- Audio file upload with drag & drop support (MP3, WAV, M4A, FLAC, OGG, WEBM)
- Browser-based audio recording (up to 30 seconds)
- Real-time transcription using Whisper (GPU-accelerated with RTX 5090)
- Multiple Whisper model support (tiny, base, small, medium, large, turbo)
- Model download progress tracking with real-time SSE updates
- **Audio playback and download** - Play audio inline or download original files
  - Play button for streaming playback
  - Download button for saving files locally
- Transcription history with delete functionality
- Editable transcription text
- Language selection support
- Dark mode UI
```

#### Step 6.3: Update This Plan Document

**File**: `AUDIO_DOWNLOAD_FEATURE_PLAN.md`
**Section**: Add "Implementation Complete" timestamp and summary when done

---

## Rollback Plan

### If Issues Arise During Implementation:

#### Backend Rollback
**File**: `src/presentation/api/routers/transcription_router.py`

1. Remove `download` query parameter from function signature
2. Remove `headers` dictionary creation
3. Remove `headers` parameter from `FileResponse`
4. Restore to original version (streaming only)

**Git Command**:
```bash
git checkout HEAD -- src/presentation/api/routers/transcription_router.py
```

#### Frontend Rollback

**History Component**:
```bash
git checkout HEAD -- src/presentation/frontend/src/app/features/history/history.component.html
git checkout HEAD -- src/presentation/frontend/src/app/features/history/history.component.ts
git checkout HEAD -- src/presentation/frontend/src/app/features/history/history.component.css
```

**Transcription Details Component**:
```bash
git checkout HEAD -- src/presentation/frontend/src/app/features/transcription/transcription.component.html
git checkout HEAD -- src/presentation/frontend/src/app/features/transcription/transcription.component.ts
git checkout HEAD -- src/presentation/frontend/src/app/features/transcription/transcription.component.css
```

**Services**:
```bash
git checkout HEAD -- src/presentation/frontend/src/app/core/services/api.service.ts
git checkout HEAD -- src/presentation/frontend/src/app/core/services/transcription.service.ts
```

### Complete Rollback (All Changes)
```bash
git checkout HEAD -- src/presentation/api/routers/transcription_router.py
git checkout HEAD -- src/presentation/frontend/src/app/features/history/
git checkout HEAD -- src/presentation/frontend/src/app/features/transcription/
git checkout HEAD -- src/presentation/frontend/src/app/core/services/
```

---

## Files Modified Summary

### Backend (1 file)
1. ✅ `src/presentation/api/routers/transcription_router.py` - Add download parameter

### Frontend Services (2 files)
2. ✅ `src/presentation/frontend/src/app/core/services/api.service.ts` - Add download URL method
3. ✅ `src/presentation/frontend/src/app/core/services/transcription.service.ts` - Add download URL method

### Frontend History Component (3 files)
4. ✅ `src/presentation/frontend/src/app/features/history/history.component.html` - Add download button
5. ✅ `src/presentation/frontend/src/app/features/history/history.component.ts` - Add download method
6. ✅ `src/presentation/frontend/src/app/features/history/history.component.css` - Add download button styles

### Frontend Details Component (3 files)
7. ✅ `src/presentation/frontend/src/app/features/transcription/transcription.component.html` - Add download button
8. ✅ `src/presentation/frontend/src/app/features/transcription/transcription.component.ts` - Add download method
9. ✅ `src/presentation/frontend/src/app/features/transcription/transcription.component.css` - Add download button styles

### Documentation (2 files)
10. ✅ `CLAUDE.md` - Document download feature
11. ✅ `README.md` (optional) - Add to features list

**Total Files Modified**: 11 files

---

## Implementation Checklist

### Pre-Implementation
- [x] Codebase structure analyzed
- [x] Existing patterns identified
- [x] Requirements clarified with user
- [x] Detailed plan created
- [x] Impact analysis completed

### Backend Implementation
- [ ] Modify audio endpoint in `transcription_router.py`
- [ ] Test endpoint with `download=false` (streaming)
- [ ] Test endpoint with `download=true` (download)
- [ ] Test error scenarios (404, missing file)

### Frontend Services Implementation
- [ ] Add `getAudioDownloadUrl()` to `api.service.ts`
- [ ] Add `getAudioDownloadUrl()` to `transcription.service.ts`

### History Component Implementation
- [ ] Add download button to template
- [ ] Add `downloadAudio()` method to component
- [ ] Add CSS styles for download button
- [ ] Test download functionality
- [ ] Test event propagation (no card navigation)
- [ ] Test with play/delete buttons (no interference)

### Details Component Implementation
- [ ] Add download button to template
- [ ] Add `downloadAudio()` method to component
- [ ] Add CSS styles for download button
- [ ] Test download functionality
- [ ] Test with play button (no interference)
- [ ] Test with tab switching

### Testing
- [ ] Run all backend tests
- [ ] Run all frontend tests
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Edge
- [ ] Regression testing (existing features work)

### Documentation
- [ ] Update `CLAUDE.md` with download feature
- [ ] Update `README.md` with download feature
- [ ] Mark this plan as complete

### Post-Implementation
- [ ] Create git commit with proper message
- [ ] Verify all files committed
- [ ] Final smoke test

---

## Risk Assessment

### High Risk Areas
**NONE** - This is a low-risk, additive feature

### Medium Risk Areas
- ✅ **Event Propagation**: Download button click might trigger card navigation in History view
  - **Mitigation**: Use `event.stopPropagation()` in click handler
  - **Testing**: Verify card navigation doesn't trigger when clicking download

### Low Risk Areas
- ✅ **CSS Conflicts**: New button styles might conflict with existing styles
  - **Mitigation**: Use specific class names (`.btn-download-small`, `.btn-download`)
  - **Testing**: Visual regression testing in both views

- ✅ **Browser Compatibility**: Download mechanism might fail in some browsers
  - **Mitigation**: Use standard `<a>` element download pattern
  - **Testing**: Cross-browser testing (Chrome, Firefox, Edge, Safari)

### Zero Risk Areas
- ✅ **Database**: No schema changes
- ✅ **Domain Logic**: No business logic changes
- ✅ **Authentication**: No auth changes
- ✅ **API Breaking Changes**: Query parameter is optional, backward compatible

---

## Success Criteria

### Functional Success
- ✅ Download button visible in History view (icon only)
- ✅ Download button visible in Details view (icon + text)
- ✅ Clicking download triggers immediate browser download
- ✅ Downloaded file has original filename
- ✅ Download works for all transcription statuses
- ✅ Download doesn't interfere with play/delete functionality

### Technical Success
- ✅ No console errors during download
- ✅ No breaking of existing functionality
- ✅ Clean architecture maintained
- ✅ Code follows existing patterns
- ✅ All tests pass

### Documentation Success
- ✅ `CLAUDE.md` updated with download feature
- ✅ `README.md` updated with download feature (if applicable)
- ✅ Code comments added where needed

---

## Notes for Implementation

1. **Test After Each Phase**: Don't wait until the end to test
2. **Commit Frequently**: Commit after each component is complete
3. **Verify Backward Compatibility**: Ensure play button still works after changes
4. **Check Console for Errors**: Monitor browser console during testing
5. **Test Multiple Audio Formats**: Verify download works for MP3, WAV, M4A, etc.
6. **Test Large Files**: Ensure download doesn't timeout for large audio files
7. **Verify Original Filename**: Check that downloaded files have correct names

---

**Plan Created**: 2024-12-30
**Plan Status**: ✅ READY FOR IMPLEMENTATION
**Estimated Total Time**: ~2 hours (including testing)
