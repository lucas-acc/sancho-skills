# Sancho Skills

个人技能集合，为 OpenClaw 提供各种实用工具。

Personal skill collection providing practical tools for OpenClaw.

---

## Skills Overview | 技能概览

| Skill | 图标 | 功能 Purpose | 亮点 Highlights |
|-------|------|--------------|-----------------|
| [audio-download](skills/audio-download/) | 🎵 | **EN**: Download audio from YouTube & Twitter/X<br>**ZH**: 从 YouTube 和 Twitter/X 下载音频 | • Multi-format support (MP3/M4A/WAV/FLAC/OGG)<br>• Playlist batch download<br>• Metadata & thumbnail embedding |
| [audio-to-text](skills/audio-to-text/) | 🎯 | **EN**: Transcribe audio to text (Chinese/English)<br>**ZH**: 语音转文字，自动识别中英文 | • Apple Silicon optimized (mlx-whisper)<br>• 5-hour long audio support<br>• Multiple formats (txt/srt/json) |
| [podcast-download](skills/podcast-download/) | 🎙️ | **EN**: Download podcasts from 小宇宙 & Apple Podcasts<br>**ZH**: 下载小宇宙和 Apple Podcasts 播客 | • Auto platform detection<br>• Smart filename with date/title<br>• RSS feed parsing |
| [pdf-to-txt](skills/pdf-to-txt/) | 📄 | **EN**: Convert PDF to plain text<br>**ZH**: 将 PDF 转换为纯文本 | • Markdown output support<br>• Page range selection<br>• Preserves document structure |
| [task-manager](skills/task-manager/) | 📝 | **EN**: Personal task management with reminders<br>**ZH**: 个人任务管理，支持每日提醒 | • SQLite + JSON backup<br>• Priority & project tagging<br>• Daily cron reminders |

---

## Quick Start | 快速开始

Each skill contains a `SKILL.md` with detailed usage instructions.

每个技能目录下都有 `SKILL.md` 提供详细使用说明。

```bash
skills/
├── audio-download/      # 🎵 Audio download
├── audio-to-text/       # 🎯 Speech-to-text
├── podcast-download/    # 🎙️ Podcast download
├── pdf-to-txt/          # 📄 PDF conversion
└── task-manager/        # 📝 Task management
```

---

## Development | 开发

See [CLAUDE.md](CLAUDE.md) for skill development guidelines.

开发规范请参考 [CLAUDE.md](CLAUDE.md)。
