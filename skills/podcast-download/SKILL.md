---
name: podcast-download
description: Download podcast episodes from 小宇宙 (Xiaoyuzhou.fm), Apple Podcasts, and RSS feeds
metadata:
  openclaw:
    emoji: 🎙️
    requires:
      bins: ["python3"]
      python_packages: ["feedparser", "requests"]
    install:
      - id: "pip-feedparser"
        kind: "uv"
        package: "feedparser"
        label: "Install feedparser for RSS parsing"
      - id: "pip-requests"
        kind: "uv"
        package: "requests"
        label: "Install requests for HTTP API calls"
---

# Podcast Download Skill

Download podcast episodes from multiple platforms with a unified interface.

## Supported Platforms

- **小宇宙 (Xiaoyuzhou.fm)**: Chinese podcast platform
- **Apple Podcasts**: Global podcast directory
- **Generic RSS Feeds**: Any valid podcast RSS feed

## Features

- Automatic platform detection from URLs
- Episode listing without downloading
- Selective episode download (specific episodes or latest N)
- Metadata preservation (title, description, publish date)
- Custom output directory and naming

## URL Formats

### 小宇宙 (Xiaoyuzhou.fm)
```
https://www.xiaoyuzhoufm.com/podcast/<podcast_id>
https://xiaoyuzhoufm.com/podcast/<podcast_id>
```

### Apple Podcasts
```
https://podcasts.apple.com/<country>/podcast/<name>/id<podcast_id>
https://podcasts.apple.com/podcast/<name>/id<podcast_id>
```

### Generic RSS Feeds
```
https://example.com/feed.xml
https://example.com/podcast/rss
```

## Basic Usage

### List Episodes (without downloading)

```bash
# List all episodes from a podcast
python {baseDir}/scripts/download.py "<URL>" --list

# List only the latest 10 episodes
python {baseDir}/scripts/download.py "<URL>" --list --limit 10
```

### Download Episodes

```bash
# Download the latest episode
python {baseDir}/scripts/download.py "<URL>" --latest

# Download the latest 5 episodes
python {baseDir}/scripts/download.py "<URL>" --latest --limit 5

# Download a specific episode by index (from --list output)
python {baseDir}/scripts/download.py "<URL>" --episode 3

# Download multiple specific episodes
python {baseDir}/scripts/download.py "<URL>" --episode 1,3,5

# Download all episodes
python {baseDir}/scripts/download.py "<URL>" --all
```

### Output Options

```bash
# Specify output directory
python {baseDir}/scripts/download.py "<URL>" --latest --output ~/Downloads/Podcasts

# Custom filename template
python {baseDir}/scripts/download.py "<URL>" --latest --template "{date}_{title}.{ext}"
```

## Examples by Platform

### 小宇宙 (Xiaoyuzhou.fm)

```bash
# List episodes from a 小宇宙 podcast
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/podcast/123456" --list

# Download the latest episode
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/podcast/123456" --latest
```

### Apple Podcasts

```bash
# List episodes from Apple Podcasts
python {baseDir}/scripts/download.py "https://podcasts.apple.com/us/podcast/example/id123456789" --list

# Download latest 3 episodes
python {baseDir}/scripts/download.py "https://podcasts.apple.com/us/podcast/example/id123456789" --latest --limit 3
```

### Generic RSS Feed

```bash
# List episodes from RSS feed
python {baseDir}/scripts/download.py "https://example.com/podcast/feed.xml" --list

# Download all episodes
python {baseDir}/scripts/download.py "https://example.com/podcast/feed.xml" --all
```

## Filename Template Variables

Use these variables in the `--template` option:

- `{title}` - Episode title
- `{date}` - Publish date (YYYYMMDD format)
- `{podcast}` - Podcast/channel name
- `{index}` - Episode index (001, 002, etc.)
- `{ext}` - File extension (mp3, m4a, etc.)

Default template: `{date}_{title}.{ext}`

## Troubleshooting

### "Failed to fetch RSS feed"

- Check your internet connection
- For 小宇宙: RSSHub might be temporarily unavailable, try again later
- For Apple Podcasts: Verify the podcast ID is correct

### "No audio enclosure found"

- The RSS feed might not contain downloadable audio files
- Some podcasts use non-standard RSS formats

### "Permission denied"

- Ensure the output directory is writable
- Try specifying a different output directory with `--output`
