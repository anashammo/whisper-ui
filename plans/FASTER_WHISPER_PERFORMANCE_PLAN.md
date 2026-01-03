# faster-whisper Performance Enhancement Plan

## Executive Summary

Performance testing revealed a critical issue: **VAD causes 5x slowdown** instead of speeding up transcription. This plan addresses the root cause and provides optimization strategies for Arabic language transcription.

## Performance Test Results (January 2026)

**Test Conditions:**
- Audio: 30-second Arabic news broadcast
- Model: large (Systran/faster-whisper-large-v3)
- GPU: NVIDIA RTX 5090 (CUDA 12.8)
- Language: Arabic (ar)

| Configuration | Processing Time | Real-time Factor |
|--------------|-----------------|------------------|
| **Without VAD** | 4.36 seconds | 6.9x real-time |
| **With VAD** | 22.0 seconds | 1.4x real-time |
| **Slowdown Factor** | **5x slower with VAD** | - |

---

## Root Cause Analysis

### Why VAD is Slow

According to [GitHub Issue #364](https://github.com/guillaumekln/faster-whisper/issues/364):

1. **RNN-based Architecture**: Silero VAD uses an RNN model that processes sequentially
2. **CPU-only Execution**: VAD runs on a single CPU thread, not GPU
3. **Small Window Size**: Default `window_size_samples=1024` requires many forward passes
4. **Short Audio Penalty**: Overhead is more noticeable for short audio files

### Current Implementation Analysis

**File:** `src/infrastructure/services/faster_whisper_service.py:310-326`

```python
vad_parameters = None
if vad_filter:
    vad_parameters = {
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 200,
    }
```

**Missing optimizations:**
- No `window_size_samples` configuration (uses slow default 1024)
- No `threshold` tuning for Arabic speech patterns
- No batched inference utilization

---

## Optimization Strategies

### Phase 1: VAD Window Optimization (Quick Fix)

**Expected Improvement:** 2x faster VAD processing

**Change:**
```python
vad_parameters = {
    "min_silence_duration_ms": 500,
    "speech_pad_ms": 200,
    "window_size_samples": 1536,  # Increase from default 1024
    "threshold": 0.5,  # Default is 0.5, tune for Arabic if needed
}
```

**Implementation:**
- [ ] Update `faster_whisper_service.py` with optimized VAD parameters
- [ ] Test with Arabic audio to verify quality maintained

---

### Phase 2: Batched Inference Pipeline (Major Performance Gain)

**Expected Improvement:** 3-12x faster overall

According to [Mobius ML blog](https://mobiusml.github.io/batched_whisper_blog/), batched inference achieves:
- 12.5x average speedup over OpenAI Whisper
- 104x real-time on GPU for medium model
- Up to 380x real-time for long audio files

**Implementation:**

**File:** `src/infrastructure/services/faster_whisper_service.py`

```python
from faster_whisper import WhisperModel, BatchedInferencePipeline

class FasterWhisperService:
    def __init__(self, settings: Settings):
        # ... existing init ...
        self.batched_models: Dict[str, BatchedInferencePipeline] = {}

    def _create_batched_model(self, model_name: str) -> BatchedInferencePipeline:
        """Create batched inference pipeline for a model."""
        base_model = self._load_model_sync(model_name)
        return BatchedInferencePipeline(model=base_model)

    def _transcribe_sync_batched(
        self,
        audio_file_path: str,
        language: Optional[str],
        batched_model: BatchedInferencePipeline,
        vad_filter: bool
    ) -> Dict[str, any]:
        """Use batched inference for faster processing."""
        segments, info = batched_model.transcribe(
            audio_file_path,
            language=language,
            batch_size=16,  # Optimal for RTX 5090 with 32GB VRAM
        )
        # Note: BatchedInferencePipeline has built-in VAD
        # vad_filter parameter may be ignored

        text_parts = [segment.text.strip() for segment in segments]
        return {
            "text": " ".join(text_parts).strip() or "(No speech detected)",
            "language": info.language,
            "duration": info.duration
        }
```

**Tasks:**
- [ ] Add `BatchedInferencePipeline` wrapper to service
- [ ] Implement `batch_size` configuration (default: 16 for RTX 5090)
- [ ] Benchmark batched vs non-batched performance
- [ ] Note: Batched mode has built-in VAD, separate `vad_filter` may be ignored

**Caveats:**
- Higher VRAM usage (~19GB for batch_size=80)
- Quality may decrease with batching (per [GitHub Issue #954](https://github.com/SYSTRAN/faster-whisper/issues/954))
- Set `use_vad_model=False` if quality issues occur

---

### Phase 3: beam_size Optimization (Speed vs Accuracy Tradeoff)

**Expected Improvement:** 30-50% faster with beam_size=1

According to [faster-whisper docs](https://github.com/SYSTRAN/faster-whisper):
- Default `beam_size=5` provides best accuracy
- `beam_size=1` (greedy decoding) is 30-50% faster
- ~2-3% accuracy loss acceptable for tiny/base models

**Recommendation for Arabic:**
```python
# For large/turbo models (accuracy priority)
beam_size = 5

# For base/small models (speed priority)
beam_size = 1  # Greedy decoding
```

**Tasks:**
- [ ] Add configurable `beam_size` parameter to transcription
- [ ] Test Arabic transcription accuracy with beam_size=1 vs beam_size=5
- [ ] Consider model-specific beam_size defaults

---

### Phase 4: condition_on_previous_text Optimization

**Expected Improvement:** Improved accuracy for long audio, prevents error propagation

```python
segments, info = model.transcribe(
    audio_file_path,
    language=language,
    beam_size=5,
    condition_on_previous_text=False,  # Prevent hallucination propagation
    vad_filter=vad_filter,
    vad_parameters=vad_parameters
)
```

**When to use:**
- `condition_on_previous_text=True` (default): Better for short, continuous speech
- `condition_on_previous_text=False`: Better for long audio, prevents error cascading

**Tasks:**
- [ ] Add as optional parameter
- [ ] Default to `False` for audio > 60 seconds
- [ ] Test with Arabic broadcast recordings

---

### Phase 5: Compute Type Optimization

**Current:** `float16` on GPU

**Alternatives:**
| Compute Type | Speed | VRAM | Accuracy | Use Case |
|-------------|-------|------|----------|----------|
| `float16` | Fast | 50% | Best | Current (good) |
| `int8_float16` | Faster | 30% | Good | Memory-constrained |
| `int8` | Fastest | 25% | Acceptable | CPU or low VRAM |

**Recommendation:** Stay with `float16` for RTX 5090 (sufficient VRAM)

---

## Recommended Implementation Order

### Priority 1: Quick Wins (No Code Changes Required)

1. **Disable VAD for short audio (<30 seconds)**
   - VAD overhead outweighs benefits for short clips
   - Current test: 4.36s without VAD vs 22s with VAD
   - **Recommendation: Make VAD opt-in, not default**

2. **VAD Window Size Optimization**
   - Change `window_size_samples` from 1024 to 1536
   - Expected: 2x faster VAD processing

### Priority 2: Batched Inference (Requires Code Changes)

1. **Implement BatchedInferencePipeline**
   - Expected: 3-12x overall speedup
   - Best for audio > 1 minute
   - Higher VRAM usage

2. **Add batch_size configuration**
   - Default: 16 for RTX 5090
   - Configurable via environment variable

### Priority 3: Fine-tuning (Optional)

1. **beam_size optimization** per model
2. **condition_on_previous_text** for long audio
3. **Arabic-specific threshold tuning** for VAD

---

## Performance Targets

| Scenario | Current | Target | Improvement |
|----------|---------|--------|-------------|
| 30s audio (no VAD) | 4.36s | 3s | 1.5x |
| 30s audio (with VAD) | 22.0s | 5s | 4.4x |
| 5min audio (batched) | ~45s | 10s | 4.5x |
| Real-time factor (large) | 6.9x | 20x | 3x |

---

## Testing Checklist

### Phase 1: VAD Optimization
- [ ] Test with `window_size_samples=1536`
- [ ] Compare processing time vs default
- [ ] Verify transcription quality unchanged
- [ ] Test with Arabic audio samples

### Phase 2: Batched Inference
- [ ] Implement BatchedInferencePipeline
- [ ] Benchmark batch_size=8, 16, 32
- [ ] Test VRAM usage at each batch size
- [ ] Compare quality vs non-batched

### Phase 3: Integration Testing
- [ ] Test all models (tiny, base, small, medium, large, turbo)
- [ ] Test Arabic language specifically
- [ ] Verify frontend compatibility
- [ ] Update documentation

---

## References

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [VAD Performance Issue #364](https://github.com/guillaumekln/faster-whisper/issues/364)
- [Batched Whisper Blog](https://mobiusml.github.io/batched_whisper_blog/)
- [Modal: 5 Ways to Speed Up Whisper](https://modal.com/blog/faster-transcription)
- [Modal: Choosing Whisper Variants](https://modal.com/blog/choosing-whisper-variants)
- [Cerebrium: Faster Whisper Transcription](https://www.cerebrium.ai/articles/faster-whisper-transcription-how-to-maximize-performance-for-real-time-audio-to-text)

---

## Decision Points for User

1. **VAD Default Behavior:**
   - Option A: Keep VAD disabled by default (current fastest)
   - Option B: Enable VAD only for audio > 60 seconds
   - Option C: Always enable VAD with optimized parameters

2. **Batched Inference:**
   - Option A: Implement for all audio
   - Option B: Implement only for audio > 1 minute
   - Option C: Make it user-selectable

3. **beam_size Strategy:**
   - Option A: Always use beam_size=5 (accuracy priority)
   - Option B: Use beam_size=1 for tiny/base, 5 for others
   - Option C: Make it user-configurable

**Recommendation:** Start with Priority 1 (VAD optimization) and evaluate results before proceeding to Priority 2 (batched inference).
