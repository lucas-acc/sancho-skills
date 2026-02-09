#!/usr/bin/env python3
"""
Podcast download helper script.
Supports 小宇宙 (Xiaoyuzhou.fm) single episode, Apple Podcasts, and generic RSS feeds.

Usage:
    python download.py <URL> [--output <dir>]

Examples:
    python download.py "https://www.xiaoyuzhoufm.com/episode/6982c33dc78b82389298d08d"
    python download.py "https://podcasts.apple.com/podcast/id360084272?i=1000748569801"
    python download.py "<URL>" --output ~/Downloads
"""

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

import json
import requests

# Optional import for RSS feeds
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


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


def is_apple_podcasts_episode_url(url: str) -> bool:
    """
    Check if URL is an Apple Podcasts episode link.

    Supported patterns:
    - https://podcasts.apple.com/podcast/id<podcast_id>?i=<episode_id>
    - https://podcasts.apple.com/<country>/podcast/<name>/id<podcast_id>?i=<episode_id>
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain not in ("podcasts.apple.com", "www.podcasts.apple.com"):
        return False

    # Check for episode ID in query params
    query = parse_qs(parsed.query)
    if 'i' not in query:
        return False

    # Check for podcast ID in path
    return '/id' in parsed.path and re.search(r'id\d+', parsed.path) is not None


def extract_apple_podcast_info(url: str) -> tuple:
    """
    Extract podcast ID and episode ID from Apple Podcasts URL.

    Returns (podcast_id, episode_id)
    """
    parsed = urlparse(url)

    # Extract podcast ID from path
    match = re.search(r'id(\d+)', parsed.path)
    if not match:
        raise ValueError(f"Could not extract podcast ID from URL: {url}")
    podcast_id = match.group(1)

    # Extract episode ID from query
    query = parse_qs(parsed.query)
    if 'i' not in query:
        raise ValueError(f"Could not extract episode ID from URL: {url}")
    episode_id = query['i'][0]

    return podcast_id, episode_id


def get_apple_podcast_rss_feed(podcast_id: str) -> str:
    """
    Get RSS feed URL from Apple Podcasts using iTunes Lookup API.
    """
    api_url = f"https://itunes.apple.com/lookup?id={podcast_id}&entity=podcast"

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("resultCount", 0) == 0:
            raise ValueError(f"Podcast not found: {podcast_id}")

        results = data.get("results", [])
        if not results:
            raise ValueError(f"No results for podcast: {podcast_id}")

        feed_url = results[0].get("feedUrl")
        if not feed_url:
            raise ValueError(f"No feed URL found for podcast: {podcast_id}")

        return feed_url

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch from iTunes API: {e}")


def get_episode_title_from_apple_page(url: str) -> tuple:
    """
    Extract episode title and podcast name from Apple Podcasts page.

    Returns (title, podcast_name)
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Fix encoding: Apple may not set charset properly, use apparent_encoding
        if response.encoding.lower() == 'iso-8859-1':
            response.encoding = response.apparent_encoding

        html = response.text

        # Extract title from <title> tag
        # Format: "Episode Title - Podcast Name - Apple Podcasts"
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            full_title = title_match.group(1).strip()
            # Remove " - Apple Podcasts" suffix
            full_title = re.sub(r'\s+-\s+Apple Podcasts$', '', full_title)

            # Try to split into episode title and podcast name
            parts = full_title.rsplit(' - ', 1)
            if len(parts) == 2:
                episode_title, podcast_name = parts
                return episode_title.strip(), podcast_name.strip()
            else:
                return full_title, ""

        raise ValueError("Could not extract title from page")

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch Apple Podcasts page: {e}")


def parse_rss_feed_for_episode(feed_url: str, target_title: str) -> Optional[Episode]:
    """
    Parse RSS feed and find episode matching the target title.

    Handles truncated titles from Apple Podcasts pages by cleaning up '...' suffixes.
    """
    if not HAS_FEEDPARSER:
        raise ImportError("feedparser is required for Apple Podcasts. Install with: pip install feedparser")

    try:
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            raise ValueError("No episodes found in RSS feed")

        podcast_name = feed.feed.get("title", "Unknown Podcast")

        # Clean up target title (remove truncation markers and suffixes)
        # Apple Podcasts pages often truncate titles with "..." and append " - Podcast Name"
        cleaned_target = target_title
        # Remove trailing " - Podcast Name" suffix if present
        if " - " in cleaned_target:
            cleaned_target = cleaned_target.rsplit(" - ", 1)[0]
        # Remove "..." truncation marker
        cleaned_target = cleaned_target.replace("...", "").strip()

        # Try exact match first
        for entry in feed.entries:
            title = entry.get("title", "")
            if title == target_title:
                return _entry_to_episode(entry, podcast_name)

        # Try case-insensitive match
        target_lower = target_title.lower()
        for entry in feed.entries:
            title = entry.get("title", "")
            if title.lower() == target_lower:
                return _entry_to_episode(entry, podcast_name)

        # Try partial match with cleaned title (handle truncation)
        cleaned_target_lower = cleaned_target.lower()
        for entry in feed.entries:
            title = entry.get("title", "")
            title_lower = title.lower()
            # Check if cleaned target is contained in RSS title
            if cleaned_target_lower in title_lower:
                return _entry_to_episode(entry, podcast_name)
            # Check if RSS title is contained in cleaned target
            if title_lower in cleaned_target_lower:
                return _entry_to_episode(entry, podcast_name)

        # Try fuzzy matching: find the entry with highest similarity to cleaned target
        best_match = None
        best_score = 0
        for entry in feed.entries:
            title = entry.get("title", "")
            # Simple similarity: length of common prefix
            title_lower = title.lower()
            min_len = min(len(cleaned_target_lower), len(title_lower))
            common_len = 0
            for i in range(min_len):
                if cleaned_target_lower[i] == title_lower[i]:
                    common_len += 1
                else:
                    break
            # Score based on common prefix ratio
            score = common_len / max(len(cleaned_target_lower), len(title_lower))
            if score > best_score and score > 0.5:  # At least 50% match
                best_score = score
                best_match = entry

        if best_match:
            return _entry_to_episode(best_match, podcast_name)

        raise ValueError(f"Could not find episode with title: {target_title}")

    except Exception as e:
        raise ValueError(f"Failed to parse RSS feed: {e}")


def _entry_to_episode(entry, podcast_name: str) -> Episode:
    """Convert a feedparser entry to Episode object."""
    title = entry.get("title", "Untitled")

    # Get audio URL from enclosures
    audio_url = None
    file_size = None
    if entry.enclosures:
        for enc in entry.enclosures:
            enc_type = enc.get("type", "")
            enc_url = enc.get("href", "")
            if enc_type.startswith("audio/") or enc_url.endswith((".mp3", ".m4a", ".aac", ".ogg")):
                audio_url = enc_url
                file_size = enc.get("length")
                break

    if not audio_url and entry.enclosures:
        # Take first enclosure if no audio type found
        audio_url = entry.enclosures[0].get("href", "")
        file_size = entry.enclosures[0].get("length")

    if not audio_url:
        raise ValueError(f"No audio URL found for episode: {title}")

    # Parse date
    pub_date = entry.get("published", entry.get("updated", ""))
    try:
        # Try common RSS date formats
        from time import mktime
        import time
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime.fromtimestamp(mktime(entry.published_parsed))
        else:
            # Try parsing the date string
            try:
                published = datetime.strptime(pub_date[:25], "%a, %d %b %Y %H:%M:%S")
            except:
                published = datetime.now()
    except:
        published = datetime.now()

    # Description
    description = entry.get("description", entry.get("summary", ""))

    # Duration
    duration = entry.get("itunes_duration", "")

    return Episode(
        title=title,
        description=description,
        published=published,
        audio_url=audio_url,
        podcast_name=podcast_name,
        duration=duration,
        file_size=int(file_size) if file_size else None
    )


def parse_apple_podcasts_episode(url: str) -> Episode:
    """
    Parse Apple Podcasts episode page to extract audio URL.

    Process:
    1. Extract podcast ID and episode ID from URL
    2. Get RSS feed URL from iTunes API
    3. Extract episode title from Apple Podcasts page
    4. Find matching episode in RSS feed
    """
    try:
        # Extract IDs
        podcast_id, episode_id = extract_apple_podcast_info(url)

        # Get RSS feed URL
        print(f"   Fetching podcast feed...")
        feed_url = get_apple_podcast_rss_feed(podcast_id)

        # Get episode title from Apple page
        print(f"   Extracting episode info...")
        title, _ = get_episode_title_from_apple_page(url)

        # Find episode in RSS feed
        print(f"   Searching for: {title}")
        episode = parse_rss_feed_for_episode(feed_url, title)

        return episode

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch Apple Podcasts data: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse Apple Podcasts episode: {e}")


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


def detect_platform(url: str) -> str:
    """Detect the platform from the URL."""
    if is_xiaoyuzhou_episode_url(url):
        return "xiaoyuzhou"
    elif is_apple_podcasts_episode_url(url):
        return "apple"
    else:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Download podcast episode from 小宇宙 (Xiaoyuzhou.fm) or Apple Podcasts"
    )
    parser.add_argument("url", help="Episode URL (e.g., https://www.xiaoyuzhoufm.com/episode/<id> or https://podcasts.apple.com/...)")
    parser.add_argument("-o", "--output", type=Path, default=Path.home() / "Downloads", help="Output directory (default: ~/Downloads)")
    parser.add_argument("--template", type=str, default="{date}_{title}.{ext}", help="Filename template")

    args = parser.parse_args()

    try:
        platform = detect_platform(args.url)

        if platform == "xiaoyuzhou":
            print(f"🔍 Platform: 小宇宙 (Xiaoyuzhou.fm)")
            print(f"📥 Parsing episode...")
            episode = parse_xiaoyuzhou_episode(args.url)
        elif platform == "apple":
            print(f"🔍 Platform: Apple Podcasts")
            print(f"📥 Resolving episode...")
            episode = parse_apple_podcasts_episode(args.url)
        else:
            print(f"Error: Unsupported URL format", file=sys.stderr)
            print(f"Supported platforms:", file=sys.stderr)
            print(f"  - 小宇宙: https://www.xiaoyuzhoufm.com/episode/<id>", file=sys.stderr)
            print(f"  - Apple Podcasts: https://podcasts.apple.com/...?i=<episode_id>", file=sys.stderr)
            return 1

        print(f"📻 {episode.podcast_name} - {episode.title}")

        print(f"\n⬇️  Downloading...")
        output_path = download_episode(episode, args.output, args.template)

        print(f"\n✅ Saved to: {output_path}")
        return 0

    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
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
