#!/usr/bin/env python3
"""
Podcast download helper script.
Supports 小宇宙 (Xiaoyuzhou.fm) single episode, Apple Podcasts, and generic RSS feeds.

Usage:
    python download.py <URL> [--output <dir>]

Examples:
    python download.py "https://www.xiaoyuzhoufm.com/episode/6982c33dc78b82389298d08d"
    python download.py "https://www.xiaoyuzhoufm.com/episode/6982c33dc78b82389298d08d" --output ~/Downloads
"""

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import json
import requests


@dataclass
class Episode:
    """Represents a podcast episode."""
    title: str
    description: str
    published: datetime
    audio_url: str
    podcast_name: str = ""
    duration: Optional[str] = None
    file_size: Optional[int] = None

    def format_filename(self, template: str = "{date}_{title}.{ext}") -> str:
        """Generate filename based on template."""
        date_str = self.published.strftime("%Y%m%d")
        safe_title = "".join(c for c in self.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')

        # Extract extension from audio_url
        ext = Path(urlparse(self.audio_url).path).suffix[1:] or "mp3"

        filename = template.format(
            title=safe_title,
            date=date_str,
            podcast=self.podcast_name,
            ext=ext
        )
        return filename


def is_xiaoyuzhou_episode_url(url: str) -> bool:
    """Check if URL is a 小宇宙 single episode link."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain not in ("xiaoyuzhoufm.com", "www.xiaoyuzhoufm.com"):
        return False

    return re.match(r'^/episode/([^/]+)/?$', parsed.path) is not None


def extract_json_from_html(html: str, key: str) -> dict:
    """
    Extract a JSON object from HTML by key using bracket matching.
    Handles nested objects correctly.
    """
    pattern = f'"{key}":'
    start = html.find(pattern)
    if start < 0:
        raise ValueError(f"Could not find '{key}' in page")

    # Start after the key and colon
    json_start = start + len(pattern)

    # Find the opening brace
    while json_start < len(html) and html[json_start] != '{':
        json_start += 1

    if json_start >= len(html):
        raise ValueError(f"Could not find JSON object for '{key}'")

    # Match braces to find the end of the object
    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(html[json_start:]):
        if escape_next:
            escape_next = False
            continue
        if char == '\\':
            escape_next = True
            continue
        if char == '"' and not in_string:
            in_string = True
        elif char == '"' and in_string:
            in_string = False
        elif char == '{' and not in_string:
            brace_count += 1
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0:
                json_str = html[json_start:json_start + i + 1]
                return json.loads(json_str)

    raise ValueError(f"Could not find matching braces for '{key}'")


def parse_xiaoyuzhou_episode(url: str) -> Episode:
    """
    Parse 小宇宙 single episode page to extract audio URL.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # Extract episode JSON data using bracket matching
        episode_data = extract_json_from_html(html, "episode")

        # Get audio URL from enclosure or media
        audio_url = None
        enclosure = episode_data.get("enclosure")
        if enclosure and isinstance(enclosure, dict):
            audio_url = enclosure.get("url")

        if not audio_url:
            media = episode_data.get("media")
            if media and isinstance(media, dict):
                source = media.get("source", {})
                if isinstance(source, dict):
                    audio_url = source.get("url")

        if not audio_url:
            raise ValueError("Could not find audio URL in episode data")

        # Parse date
        pub_date = episode_data.get("pubDate", "")
        try:
            published = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        except:
            published = datetime.now()

        # Get podcast name from podcast info
        podcast_name = ""
        podcast_data = episode_data.get("podcast", {})
        if isinstance(podcast_data, dict):
            podcast_name = podcast_data.get("title", "")

        # Duration in seconds
        duration_sec = episode_data.get("duration", 0)
        duration = str(duration_sec) if duration_sec else ""

        # File size - prefer media.size over enclosure.length
        file_size = None
        media = episode_data.get("media")
        if isinstance(media, dict):
            file_size = media.get("size")
        if not file_size and isinstance(enclosure, dict):
            file_size = enclosure.get("length")

        return Episode(
            title=episode_data.get("title", "Untitled"),
            description=episode_data.get("description", ""),
            published=published,
            audio_url=audio_url,
            podcast_name=podcast_name,
            duration=duration,
            file_size=int(file_size) if file_size else None
        )

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch 小宇宙 episode: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse 小宇宙 data: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse 小宇宙 episode: {e}")


def download_episode(episode: Episode, output_dir: Path, template: str = "{date}_{title}.{ext}") -> Path:
    """
    Download a single episode.

    Returns the downloaded file path on success.
    """
    filename = episode.format_filename(template)
    output_path = output_dir / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  ⏭️  Skipping (exists): {filename}")
        return output_path

    print(f"  ⬇️  Downloading: {episode.title}")
    print(f"     -> {output_path}")

    try:
        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download with urllib
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        req = urllib.request.Request(episode.audio_url, headers=headers)

        with urllib.request.urlopen(req, timeout=60) as response:
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        print(f"     ✅ Complete")
        return output_path

    except urllib.error.HTTPError as e:
        raise ConnectionError(f"HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"URL Error: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Download podcast episode from 小宇宙 (Xiaoyuzhou.fm)"
    )
    parser.add_argument("url", help="Episode URL (e.g., https://www.xiaoyuzhoufm.com/episode/<id>)")
    parser.add_argument("-o", "--output", type=Path, default=Path.home() / "Downloads", help="Output directory (default: ~/Downloads)")
    parser.add_argument("--template", type=str, default="{date}_{title}.{ext}", help="Filename template")

    args = parser.parse_args()

    try:
        if not is_xiaoyuzhou_episode_url(args.url):
            print(f"Error: URL does not appear to be a 小宇宙 episode link", file=sys.stderr)
            print(f"Expected format: https://www.xiaoyuzhoufm.com/episode/<id>", file=sys.stderr)
            return 1

        print(f"🔍 Parsing episode...")
        episode = parse_xiaoyuzhou_episode(args.url)
        print(f"📻 {episode.podcast_name} - {episode.title}")

        print(f"\n📥 Downloading...")
        output_path = download_episode(episode, args.output, args.template)

        print(f"\n✅ Saved to: {output_path}")
        return 0

    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
