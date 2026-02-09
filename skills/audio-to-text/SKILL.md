---
name: audio-to-text
description: Transcribe audio files to text with automatic language detection (supports Chinese and English)
metadata:
  openclaw:
    emoji: 📝
    requires:
      bins: ["python3", "ffmpeg"]
      python_packages: ["mlx-whisper"]
    install:
      - id: "pip-mlx-whisper"
        kind: "pip"
        command: "pip install mlx-whisper"
        label: "Install mlx-whisper"
      - id: "brew-ffmpeg"
        kind: "brew"
        formula: "ffmpeg"
        bins: ["ffmpeg"]
        label: "Install ffmpeg"
---

# Audio to Text Skill

Transcribe audio files to text with automatic language detection.

## Features

- **Apple Silicon optimized** using mlx-whisper
- Automatic language detection (Chinese/English)
- Chunked processing for long audio files (up to 5 hours)
- Resume from interruption support
- Progress tracking
- Multiple output formats (txt, srt, json)

## Usage

### Basic Transcription

```bash
# Transcribe to default output (same directory as input)
python {baseDir}/scripts/transcribe.py "<audio_file>"

# Transcribe with custom output path
python {baseDir}/scripts/transcribe.py "<audio_file>" -o output.txt

# Use specific model (default: small)
python {baseDir}/scripts/transcribe.py "<audio_file>" --model medium
```

### Options

- `--model`: Model size (tiny, base, small, medium, large-v3). Default: small
- `--chunk-minutes`: Minutes per chunk for long audio. Default: 15
- `--format`: Output format (txt, srt, json). Default: txt
- `--language`: Force specific language (auto-detect if not specified)

## Examples

```bash
python {baseDir}/scripts/transcribe.py podcast.mp3
python {baseDir}/scripts/transcribe.py interview.wav -o transcript.txt --model medium
python {baseDir}/scripts/transcribe.py lecture.mp3 --format srt --chunk-minutes 10
```

## Output Format

### TXT Format
Plain text with paragraphs.

### SRT Format
SubRip subtitle format with timestamps.

### JSON Format
```json
{
  "language": "zh",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "..."}
  ],
  "text": "..."
}
```

## Troubleshooting

### Out of Memory
Use a smaller model or increase chunk size.

### First Run Slow
The first run will download the model from Hugging Face (150MB-3GB depending on model size).

### Performance
mlx-whisper is optimized for Apple Silicon and runs ~30% faster than other implementations on M-series chips.
