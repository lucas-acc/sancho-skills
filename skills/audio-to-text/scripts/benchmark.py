#!/usr/bin/env python3
"""
Benchmark script to compare faster-whisper vs mlx-whisper performance.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

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

def benchmark_faster_whisper(audio_path: Path, model: str = "small") -> dict:
    """Benchmark faster-whisper."""
    from faster_whisper import WhisperModel

    print(f"\n{'='*60}")
    print(f"Testing faster-whisper (model: {model})")
    print(f"{'='*60}")

    # Load model
    start_time = time.time()
    print(f"Loading model...")
    whisper_model = WhisperModel(model, device="auto", compute_type="auto")
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f}s")

    # Transcribe
    print(f"Transcribing...")
    start_time = time.time()
    segments, info = whisper_model.transcribe(
        str(audio_path),
        task="transcribe",
        vad_filter=True
    )

    # Consume all segments (generator)
    results = list(segments)
    transcribe_time = time.time() - start_time

    # Get text
    text = " ".join(seg.text.strip() for seg in results)

    return {
        "backend": "faster-whisper",
        "model": model,
        "load_time": load_time,
        "transcribe_time": transcribe_time,
        "total_time": load_time + transcribe_time,
        "language": info.language if info else None,
        "segments_count": len(results),
        "text_sample": text[:200] + "..." if len(text) > 200 else text
    }

def benchmark_mlx_whisper(audio_path: Path, model: str = "small") -> dict:
    """Benchmark mlx-whisper."""
    import mlx_whisper

    # Map model names to mlx-whisper model paths
    # Using Apple's official mlx-community models
    model_map = {
        "tiny": "mlx-community/whisper-tiny-mlx",
        "base": "mlx-community/whisper-base-mlx",
        "small": "mlx-community/whisper-small-mlx",
        "medium": "mlx-community/whisper-medium-mlx",
        "large-v3": "mlx-community/whisper-large-v3-mlx"
    }
    mlx_model = model_map.get(model, f"mlx-community/whisper-{model}")

    print(f"\n{'='*60}")
    print(f"Testing mlx-whisper (model: {mlx_model})")
    print(f"{'='*60}")

    # mlx-whisper loads model on first transcribe, so we measure total time
    print(f"Loading model + transcribing...")
    start_time = time.time()

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=mlx_model,
        language="zh"  # Specify Chinese since it's Chinese audio
    )

    total_time = time.time() - start_time

    # Get text from result
    text = result.get("text", "")
    segments = result.get("segments", [])

    return {
        "backend": "mlx-whisper",
        "model": mlx_model,
        "load_time": 0,  # mlx-whisper combines loading and transcription
        "transcribe_time": total_time,
        "total_time": total_time,
        "language": result.get("language"),
        "segments_count": len(segments),
        "text_sample": text[:200] + "..." if len(text) > 200 else text
    }

def print_results(results: dict, audio_duration: float):
    """Print benchmark results."""
    print(f"\n{'='*60}")
    print(f"Results for {results['backend']}")
    print(f"{'='*60}")
    print(f"Model: {results['model']}")
    print(f"Model load time: {results['load_time']:.2f}s")
    print(f"Transcription time: {results['transcribe_time']:.2f}s")
    print(f"Total time: {results['total_time']:.2f}s")
    print(f"Audio duration: {audio_duration/60:.1f} minutes")
    print(f"Real-time factor: {audio_duration / results['transcribe_time']:.2f}x")
    print(f"Detected language: {results['language']}")
    print(f"Segments: {results['segments_count']}")
    print(f"Text sample: {results['text_sample'][:100]}...")

def main():
    parser = argparse.ArgumentParser(description="Benchmark whisper implementations")
    parser.add_argument("audio_file", type=Path, help="Audio file to transcribe")
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"])
    parser.add_argument("--backend", choices=["faster", "mlx", "both"], default="both",
                        help="Which backend to test")

    args = parser.parse_args()

    if not args.audio_file.exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        return 1

    # Get audio duration
    audio_duration = get_audio_duration(args.audio_file)
    print(f"Audio file: {args.audio_file}")
    print(f"Duration: {audio_duration/60:.1f} minutes ({audio_duration:.1f}s)")

    results = []

    # Test faster-whisper
    if args.backend in ["faster", "both"]:
        try:
            result = benchmark_faster_whisper(args.audio_file, args.model)
            results.append(result)
            print_results(result, audio_duration)
        except Exception as e:
            print(f"\nError with faster-whisper: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    # Test mlx-whisper
    if args.backend in ["mlx", "both"]:
        try:
            result = benchmark_mlx_whisper(args.audio_file, args.model)
            results.append(result)
            print_results(result, audio_duration)
        except Exception as e:
            print(f"\nError with mlx-whisper: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    # Print comparison summary
    if len(results) == 2:
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")

        faster_time = results[0]['transcribe_time']
        mlx_time = results[1]['transcribe_time']
        speedup = faster_time / mlx_time

        print(f"faster-whisper: {faster_time:.2f}s (real-time: {audio_duration/faster_time:.2f}x)")
        print(f"mlx-whisper:    {mlx_time:.2f}s (real-time: {audio_duration/mlx_time:.2f}x)")
        print(f"\nmlx-whisper speedup: {speedup:.2f}x")

        if speedup > 1:
            print(f"mlx-whisper is {speedup:.2f}x FASTER than faster-whisper")
        else:
            print(f"faster-whisper is {1/speedup:.2f}x FASTER than mlx-whisper")

    return 0

if __name__ == "__main__":
    sys.exit(main())
