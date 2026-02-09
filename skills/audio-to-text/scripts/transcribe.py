#!/usr/bin/env python3
"""
Audio transcription script with chunking and resume support.
Uses mlx-whisper for efficient transcription with automatic language detection.
Optimized for Apple Silicon.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# mlx-whisper import
try:
    import mlx_whisper
    HAS_MLX_WHISPER = True
except ImportError:
    HAS_MLX_WHISPER = False


class ProgressTracker:
    """Track transcription progress for resume support."""

    def __init__(self, audio_path: Path):
        self.progress_file = audio_path.parent / f".{audio_path.stem}.progress.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.progress_file.exists():
            return json.loads(self.progress_file.read_text())
        return {"completed_chunks": [], "language": None, "segments": []}

    def save(self):
        self.progress_file.write_text(json.dumps(self.data))

    def is_chunk_completed(self, chunk_idx: int) -> bool:
        return chunk_idx in self.data["completed_chunks"]

    def mark_chunk_completed(self, chunk_idx: int, segments: list):
        if chunk_idx not in self.data["completed_chunks"]:
            self.data["completed_chunks"].append(chunk_idx)
            self.data["segments"].extend(segments)
        self.save()

    def get_detected_language(self) -> Optional[str]:
        return self.data.get("language")

    def set_detected_language(self, lang: str):
        self.data["language"] = lang
        self.save()

    def get_segments(self) -> list:
        return self.data.get("segments", [])

    def cleanup(self):
        if self.progress_file.exists():
            self.progress_file.unlink()


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def split_audio(audio_path: Path, chunk_minutes: int, temp_dir: Path) -> list[Path]:
    """Split audio into chunks using ffmpeg."""
    duration = get_audio_duration(audio_path)
    chunk_seconds = chunk_minutes * 60
    chunks = []

    num_chunks = int(duration // chunk_seconds) + (1 if duration % chunk_seconds > 0 else 0)

    for i in range(num_chunks):
        start_time = i * chunk_seconds
        chunk_path = temp_dir / f"chunk_{i:04d}.wav"

        cmd = [
            "ffmpeg", "-y", "-i", str(audio_path),
            "-ss", str(start_time),
            "-t", str(chunk_seconds),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(chunk_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        chunks.append(chunk_path)

    return chunks


# Model mapping for mlx-whisper
MLX_MODEL_MAP = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large-v3": "mlx-community/whisper-large-v3-mlx"
}


def transcribe_chunk(
    chunk_path: Path,
    model_name: str,
    language: Optional[str] = None
) -> tuple[list[dict], Optional[str]]:
    """Transcribe a single audio chunk using mlx-whisper."""
    mlx_model = MLX_MODEL_MAP.get(model_name, model_name)

    result = mlx_whisper.transcribe(
        str(chunk_path),
        path_or_hf_repo=mlx_model,
        language=language,
        task="transcribe"
    )

    segments = result.get("segments", [])
    results = []
    for seg in segments:
        results.append({
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": seg.get("text", "").strip()
        })

    detected_lang = result.get("language")
    return results, detected_lang


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_output(segments: list[dict], output_path: Path, format_type: str, language: Optional[str] = None):
    """Write transcription to output file."""
    if format_type == "txt":
        text = "\n".join(seg["text"] for seg in segments)
        output_path.write_text(text, encoding="utf-8")

    elif format_type == "srt":
        lines = []
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    elif format_type == "json":
        data = {"segments": segments, "text": " ".join(seg["text"] for seg in segments)}
        if language:
            data["language"] = language
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio to text using mlx-whisper")
    parser.add_argument("audio_file", type=Path, help="Audio file to transcribe")
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"])
    parser.add_argument("--chunk-minutes", type=int, default=15, help="Minutes per chunk")
    parser.add_argument("--format", default="txt", choices=["txt", "srt", "json"])
    parser.add_argument("--language", help="Language code (auto-detect if not specified)")

    args = parser.parse_args()

    if not HAS_MLX_WHISPER:
        print("Error: mlx-whisper is required. Install with: pip install mlx-whisper", file=sys.stderr)
        return 1

    if not args.audio_file.exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        return 1

    # Setup progress tracker
    tracker = ProgressTracker(args.audio_file)

    # Use saved language detection if resuming
    detected_lang = args.language or tracker.get_detected_language()

    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Check if we need to split
        duration = get_audio_duration(args.audio_file)
        chunk_seconds = args.chunk_minutes * 60

        if duration <= chunk_seconds:
            # Short audio, transcribe directly
            print(f"Audio duration: {duration/60:.1f} minutes, transcribing directly...")
            print(f"Using model: {args.model} (mlx-whisper)")
            segments, lang = transcribe_chunk(args.audio_file, args.model, detected_lang)
            if lang:
                detected_lang = lang
        else:
            # Long audio, process in chunks
            print(f"Audio duration: {duration/60:.1f} minutes, splitting into chunks...")
            chunks = split_audio(args.audio_file, args.chunk_minutes, temp_path)
            print(f"Split into {len(chunks)} chunks")
            print(f"Using model: {args.model} (mlx-whisper)")

            all_segments = []

            for i, chunk_path in enumerate(chunks):
                if tracker.is_chunk_completed(i):
                    print(f"Chunk {i+1}/{len(chunks)}: Already completed, skipping")
                    # Load saved segments from progress
                    continue

                print(f"Chunk {i+1}/{len(chunks)}: Transcribing...", end=" ", flush=True)
                try:
                    segments, lang = transcribe_chunk(chunk_path, args.model, detected_lang)

                    # Detect language from first chunk if not specified
                    if i == 0 and lang and not detected_lang:
                        detected_lang = lang
                        tracker.set_detected_language(lang)
                        print(f"[Detected language: {lang}]")

                    # Adjust timestamps
                    offset = i * chunk_seconds
                    for seg in segments:
                        seg["start"] += offset
                        seg["end"] += offset

                    all_segments.extend(segments)
                    tracker.mark_chunk_completed(i, segments)
                    print(f"✓ ({len(segments)} segments)")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    print(f"\nProgress saved. To resume, run the command again.", file=sys.stderr)
                    return 1

            # Load previously completed segments from tracker
            saved_segments = tracker.get_segments()
            if saved_segments:
                all_segments = saved_segments + all_segments
            segments = all_segments

        # Determine output path
        output_path = args.output or args.audio_file.with_suffix(f".{args.format}")

        # Write output
        write_output(segments, output_path, args.format, detected_lang)
        print(f"\nTranscription saved to: {output_path}")
        if detected_lang:
            print(f"Detected language: {detected_lang}")

        # Cleanup progress file on success
        tracker.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
