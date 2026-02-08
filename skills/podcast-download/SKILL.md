---
name: podcast-download
description: Download podcast episodes from 小宇宙 (Xiaoyuzhou.fm)
metadata:
  openclaw:
    emoji: 🎙️
    requires:
      bins: ["python3"]
      python_packages: ["requests"]
    install:
      - id: "pip-deps"
        kind: "pip"
        command: "pip install requests"
        label: "Install Python dependency (requests)"
---

# Podcast Download Skill

Download single podcast episodes from 小宇宙 (Xiaoyuzhou.fm).

## Supported URL Format

### 小宇宙 Episode Link
```
https://www.xiaoyuzhoufm.com/episode/<episode_id>
```

Get the episode link from the 小宇宙 app or website by clicking "分享" (Share) and copying the link.

## Usage

### Basic Download

```bash
# Download to default directory (~/Downloads)
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/episode/<id>"

# Download to custom directory
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/episode/<id>" --output ~/Music
```

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

## Example

```bash
python {baseDir}/scripts/download.py "https://www.xiaoyuzhoufm.com/episode/6982c33dc78b82389298d08d"
```

Output:
```
🔍 Parsing episode...
📻 播客名称 - 单集标题

📥 Downloading...
  ⬇️  Downloading: 单集标题
     -> /Users/xxx/Downloads/20250115_单集标题.mp3
     ✅ Complete

✅ Saved to: /Users/xxx/Downloads/20250115_单集标题.mp3
```

## Troubleshooting

### "Could not find episode data in page"

- Check that the URL is a valid 小宇宙 episode link (not podcast link)
- Episode URL format: `https://www.xiaoyuzhoufm.com/episode/<id>`
- The page structure may have changed - try updating the script

### "Could not find audio URL in episode data"

- This episode may not have a downloadable audio file
- Some premium episodes may be restricted

### Download fails or is interrupted

- Check your internet connection
- Try again - 小宇宙 servers may be temporarily unavailable
