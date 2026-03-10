import os
import asyncio
from typing import Optional

from app.config import WHISPER_MODEL, WHISPER_DEVICE


_model = None


def _get_model():
    """Lazy-load the Whisper model."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type="int8" if WHISPER_DEVICE == "cpu" else "float16",
        )
    return _model


def transcribe_audio_sync(
    file_path: str,
    speaker_count: int = 2,
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe audio file using faster-whisper.
    Returns transcript text and segments with timestamps.
    """
    model = _get_model()

    segments_iter, info = model.transcribe(
        file_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        ),
    )

    segments = []
    full_text_parts = []

    for segment in segments_iter:
        seg_data = {
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
        }
        segments.append(seg_data)
        full_text_parts.append(segment.text.strip())

    full_text = " ".join(full_text_parts)

    # Build stenogram with timestamps
    stenogram_lines = []
    for seg in segments:
        minutes_s = int(seg["start"]) // 60
        seconds_s = int(seg["start"]) % 60
        minutes_e = int(seg["end"]) // 60
        seconds_e = int(seg["end"]) % 60
        time_label = f"[{minutes_s:02d}:{seconds_s:02d} - {minutes_e:02d}:{seconds_e:02d}]"
        stenogram_lines.append(f"{time_label} {seg['text']}")

    stenogram = "\n".join(stenogram_lines)

    return {
        "text": full_text,
        "stenogram": stenogram,
        "segments": segments,
        "language": info.language if info else "",
        "duration_seconds": round(info.duration, 2) if info else 0,
    }


async def transcribe_audio(
    file_path: str,
    speaker_count: int = 2,
    language: Optional[str] = None,
) -> dict:
    """Async wrapper around sync transcription."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        transcribe_audio_sync,
        file_path,
        speaker_count,
        language,
    )
