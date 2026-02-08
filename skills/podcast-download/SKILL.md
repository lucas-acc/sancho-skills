---
name: podcast-download
description: Download podcast episodes from 小宇宙 (Xiaoyuzhou.fm) and Apple Podcasts
metadata:
  openclaw:
    emoji: 🎙️
    requires:
      bins: ["python3"]
      python_packages: ["requests", "feedparser"]
    install:
      - id: "pip-deps"
        kind: "pip"
        command: "pip install requests feedparser"
        label: "Install Python dependencies (requests, feedparser)"
---

# Podcast Download Skill

Download single podcast episodes from 小宇宙 (Xiaoyuzhou.fm) and Apple Podcasts.

## Supported URL Formats

### 小宇宙 (Xiaoyuzhou.fm)
```
https://www.xiaoyuzhoufm.com/episode/<episode_id>
```

Get the episode link from the 小宇宙 app or website by clicking "分享" (Share) and copying the link.

### Apple Podcasts
```
https://podcasts.apple.com/podcast/id<podcast_id>?i=<episode_id>
```

Get the episode link from the Apple Podcasts app by clicking the share button on an episode page.

## Usage

### Basic Download

```bash
# Download to default directory (~/Downloads)
python {baseDir}/scripts/download.py "<episode_url>"

# Download to custom directory
python {baseDir}/scripts/download.py "<episode_url>" --output ~/Music
```

The script auto-detects the platform from the URL. Currently supported:
- 小宇宙 (Xiaoyuzhou.fm): `https://www.xiaoyuzhoufm.com/episode/<id>`
- Apple Podcasts: `https://podcasts.apple.com/...?i=<episode_id>`

### Filename Template

```bash
# Custom filename template
python {baseDir}/scripts/download.py "<URL>" --template "{podcast}_{date}_{title}.{ext}"
```

Available variables:
- `{title}` - Episode title
- `{date}` - Publish date (YYYYMMDD format)
- `{podcast}` - Podcast name
- `{ext}` - File extension (mp3, m4a, etc.)

Default template: `{date}_{title}.{ext}`

## Examples

### 小宇宙

```bash
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/episode/6982c33dc78b82389298d08d"
```

### Apple Podcasts

```bash
python {baseDir}/scripts/download.py "https://podcasts.apple.com/podcast/id360084272?i=1000748569801"
```

Output:
```
🔍 Platform: Apple Podcasts
📥 Resolving episode...
   Fetching podcast feed...
   Extracting episode info...
   Searching for: #2450 - Tommy Wood
📻 The Joe Rogan Experience - #2450 - Tommy Wood

⬇️  Downloading...
  ⬇️  Downloading: #2450 - Tommy Wood
     -> /Users/xxx/Downloads/20260204_2450_Tommy_Wood.mp3
     ✅ Complete

✅ Saved to: /Users/xxx/Downloads/20260204_2450_Tommy_Wood.mp3
```

## Troubleshooting

### "Could not find episode data in page" (小宇宙)

- Check that the URL is a valid 小宇宙 episode link (not podcast link)
- Episode URL format: `https://www.xiaoyuzhoufm.com/episode/<id>`
- The page structure may have changed - try updating the script

### "Could not find audio URL in episode data" (小宇宙)

- This episode may not have a downloadable audio file
- Some premium episodes may be restricted

### "Could not find episode with title" (Apple Podcasts)

- The episode might have been removed from the RSS feed
- Try using a more recent episode link
- Some episodes may have different titles in the RSS feed vs Apple Podcasts page

### "feedparser is required for Apple Podcasts"

- Install the dependency: `pip install feedparser`

### Download fails or is interrupted

- Check your internet connection
- Try again - servers may be temporarily unavailable
