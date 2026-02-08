#!/usr/bin/env python3
"""
Podcast download helper script.
Supports 小宇宙 (Xiaoyuzhou.fm), Apple Podcasts, and generic RSS feeds.
"""

import argparse
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

import feedparser
import json
import requests


@dataclass
class Episode:
    """Represents a podcast episode."""
    title: str
    description: str
    published: datetime
    audio_url: str
    duration: Optional[str] = None
    file_size: Optional[int] = None

    def format_filename(self, template: str, podcast_name: str, index: int) -> str:
        """Generate filename based on template."""
        date_str = self.published.strftime("%Y%m%d")
        safe_title = "".join(c for c in self.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')

        # Extract extension from audio_url
        ext = Path(urlparse(self.audio_url).path).suffix[1:] or "mp3"

        filename = template.format(
            title=safe_title,
            date=date_str,
            podcast=podcast_name,
            index=f"{index:03d}",
            ext=ext
        )
        return filename


@dataclass
class Podcast:
    """Represents a podcast feed."""
    title: str
    description: str
    link: str
    episodes: list

    def get_episode(self, index: int) -> Optional[Episode]:
        """Get episode by 1-based index."""
        if 1 <= index <= len(self.episodes):
            return self.episodes[index - 1]
        return None


def is_xiaoyuzhou_url(url: str) -> bool:
    """
    Check if URL is a 小宇宙 (Xiaoyuzhou.fm) podcast link.

    Supported patterns:
    - https://www.xiaoyuzhoufm.com/podcast/<id>
    - https://xiaoyuzhoufm.com/podcast/<id>
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain not in ("xiaoyuzhoufm.com", "www.xiaoyuzhoufm.com"):
        return False

    # Check path pattern: /podcast/<id>
    path_match = re.match(r'^/podcast/([^/]+)/?$', parsed.path)
    return path_match is not None


def is_apple_podcasts_url(url: str) -> bool:
    """
    Check if URL is an Apple Podcasts link.

    Supported patterns:
    - https://podcasts.apple.com/<country>/podcast/<name>/id<podcast_id>
    - https://podcasts.apple.com/podcast/<name>/id<podcast_id>
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain not in ("podcasts.apple.com", "www.podcasts.apple.com"):
        return False

    # Check path contains /podcast/ and ends with id<number>
    return "/podcast/" in parsed.path and re.search(r'/id\d+$', parsed.path) is not None


def is_rss_feed_url(url: str) -> bool:
    """
    Check if URL appears to be an RSS feed.

    Heuristic: URL ends with common feed extensions or contains 'feed', 'rss', 'podcast'
    """
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Common RSS feed indicators in path
    rss_indicators = ['feed', 'rss', 'podcast', '.xml']
    return any(indicator in path for indicator in rss_indicators)


def extract_xiaoyuzhou_podcast_id(url: str) -> str:
    """Extract podcast ID from 小宇宙 URL."""
    parsed = urlparse(url)
    match = re.match(r'^/podcast/([^/]+)/?$', parsed.path)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract podcast ID from URL: {url}")


def parse_xiaoyuzhou_page(url: str) -> Podcast:
    """
    Parse 小宇宙 podcast page directly to extract episodes.

    The page contains JSON data with episodes array including:
    - title, description, pubDate, duration
    - enclosure.url or media.source.url for audio
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # Extract JSON data containing episodes
        # Pattern: "episodes":[...] followed by podcast data
        episodes_match = re.search(r'"episodes":(\[.*?\]),"podcast":', html, re.DOTALL)
        if not episodes_match:
            raise ValueError("Could not find episodes data in page")

        episodes_json = episodes_match.group(1)
        episodes_data = json.loads(episodes_json)

        # Extract podcast info
        podcast_match = re.search(r'"podcast":({[^}]*"title"[^}]*})', html)
        podcast_title = "Unknown Podcast"
        podcast_desc = ""
        if podcast_match:
            podcast_data = json.loads(podcast_match.group(1))
            podcast_title = podcast_data.get("title", podcast_title)
            podcast_desc = podcast_data.get("description", "")

        # Parse episodes
        episodes = []
        for ep in episodes_data:
            # Get audio URL from various possible locations
            audio_url = None
            if "enclosure" in ep and ep["enclosure"]:
                audio_url = ep["enclosure"].get("url")
            elif "media" in ep and ep["media"]:
                audio_url = ep["media"].get("source", {}).get("url")

            if not audio_url:
                continue

            # Parse date
            pub_date = ep.get("pubDate", "")
            try:
                # ISO 8601 format: 2021-04-06T13:00:00.525Z
                published = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except:
                published = datetime.now()

            # Duration in seconds
            duration_sec = ep.get("duration", 0)
            duration = str(duration_sec) if duration_sec else ""

            episode = Episode(
                title=ep.get("title", "Untitled"),
                description=ep.get("description", ""),
                published=published,
                audio_url=audio_url,
                duration=duration,
                file_size=ep.get("media", {}).get("size")
            )
            episodes.append(episode)

        # Sort by published date (newest first)
        episodes.sort(key=lambda e: e.published, reverse=True)

        return Podcast(
            title=podcast_title,
            description=podcast_desc,
            link=url,
            episodes=episodes
        )

    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch 小宇宙 page: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse 小宇宙 data: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse 小宇宙 page: {e}")


def extract_apple_podcast_id(url: str) -> str:
    """Extract podcast ID from Apple Podcasts URL."""
    match = re.search(r'/id(\d+)$', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract podcast ID from URL: {url}")


def get_feed_url_from_apple_podcasts(url: str) -> str:
    """
    Get RSS feed URL from Apple Podcasts using iTunes Lookup API.

    API: https://itunes.apple.com/lookup?id=<podcast_id>&entity=podcast
    """
    podcast_id = extract_apple_podcast_id(url)
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


def get_podcast_from_url(url: str) -> Podcast:
    """
    Get Podcast object from any supported URL.

    Handles platform-specific parsing:
    - 小宇宙: Direct page parsing
    - Apple Podcasts: iTunes API + RSS
    - Generic: RSS feed parsing
    """
    if is_xiaoyuzhou_url(url):
        print(f"   Platform: 小宇宙 (Xiaoyuzhou.fm)")
        return parse_xiaoyuzhou_page(url)
    elif is_apple_podcasts_url(url):
        print(f"   Platform: Apple Podcasts")
        feed_url = get_feed_url_from_apple_podcasts(url)
        print(f"   RSS feed: {feed_url}")
        return parse_rss_feed(feed_url)
    else:
        # Treat as generic RSS feed
        print(f"   Platform: RSS Feed")
        return parse_rss_feed(url)


def parse_date(date_str: str) -> datetime:
    """
    Parse various date formats from RSS feeds.

    Tries multiple formats and returns current time if parsing fails.
    """
    if not date_str:
        return datetime.now()

    # Common RSS date formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 2822
        "%a, %d %b %Y %H:%M:%S %Z",      # RFC 2822 with TZ name
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",             # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",              # Simple format
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    # Try feedparser's parsed date if available
    try:
        from time import mktime
        import time
        struct_time = time.strptime(date_str.strip()[:25], "%a, %d %b %Y %H:%M:%S")
        return datetime.fromtimestamp(mktime(struct_time))
    except (ValueError, ImportError):
        pass

    return datetime.now()


def parse_episode(entry) -> Optional[Episode]:
    """
    Parse a single RSS entry into an Episode object.

    Extracts title, description, publish date, and audio enclosure.
    """
    # Required: title
    title = entry.get("title", "Untitled Episode")

    # Required: audio enclosure
    audio_url = None
    file_size = None
    if "enclosures" in entry and entry.enclosures:
        # Find audio enclosure (prefer mp3, but accept any audio/*)
        for enc in entry.enclosures:
            enc_type = enc.get("type", "")
            enc_url = enc.get("href", "")
            if enc_type.startswith("audio/") or enc_url.endswith((".mp3", ".m4a", ".aac", ".ogg")):
                audio_url = enc_url
                file_size = enc.get("length")
                break

    if not audio_url:
        return None  # Skip episodes without audio

    # Parse published date
    published = parse_date(entry.get("published", entry.get("updated", "")))

    # Description
    description = entry.get("description", entry.get("summary", ""))

    # Duration (itunes:duration or duration field)
    duration = entry.get("itunes_duration", entry.get("duration", ""))

    return Episode(
        title=title,
        description=description,
        published=published,
        audio_url=audio_url,
        duration=duration,
        file_size=int(file_size) if file_size else None
    )


def parse_rss_feed(feed_url: str) -> Podcast:
    """
    Parse RSS feed and return Podcast object.

    Uses feedparser to extract podcast metadata and episodes.
    """
    try:
        parsed = feedparser.parse(feed_url)

        if parsed.bozo and hasattr(parsed, 'bozo_exception'):
            # Log warning but continue if possible
            print(f"Warning: RSS parse issue: {parsed.bozo_exception}", file=sys.stderr)

        if not parsed.entries:
            raise ValueError("No episodes found in RSS feed")

        # Extract podcast metadata
        feed = parsed.feed
        podcast_title = feed.get("title", "Unknown Podcast")
        podcast_description = feed.get("description", "")
        podcast_link = feed.get("link", feed_url)

        # Parse episodes
        episodes = []
        for entry in parsed.entries:
            episode = parse_episode(entry)
            if episode:
                episodes.append(episode)

        # Sort by published date (newest first)
        episodes.sort(key=lambda e: e.published, reverse=True)

        return Podcast(
            title=podcast_title,
            description=podcast_description,
            link=podcast_link,
            episodes=episodes
        )

    except Exception as e:
        raise ConnectionError(f"Failed to parse RSS feed: {e}")


def list_episodes(podcast: Podcast, limit: Optional[int] = None) -> None:
    """Print formatted episode list."""
    print(f"\n🎙️  {podcast.title}")
    print(f"   {podcast.description[:100]}..." if len(podcast.description) > 100 else f"   {podcast.description}")
    print(f"\n   Total episodes: {len(podcast.episodes)}")
    print("-" * 80)

    episodes_to_show = podcast.episodes[:limit] if limit else podcast.episodes

    for i, episode in enumerate(episodes_to_show, 1):
        date_str = episode.published.strftime("%Y-%m-%d")
        duration_str = f" [{episode.duration}]" if episode.duration else ""
        title = episode.title[:50] + "..." if len(episode.title) > 50 else episode.title

        print(f"  {i:3d}. [{date_str}] {title}{duration_str}")

    if limit and len(podcast.episodes) > limit:
        print(f"\n   ... and {len(podcast.episodes) - limit} more episodes")


def download_episode(
    episode: Episode,
    podcast_name: str,
    index: int,
    output_dir: Path,
    template: str
) -> bool:
    """
    Download a single episode.

    Returns True on success, False on failure.
    """
    filename = episode.format_filename(template, podcast_name, index)
    output_path = output_dir / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  ⏭️  Skipping (exists): {filename}")
        return True

    print(f"  ⬇️  Downloading: {episode.title[:60]}...")
    print(f"     -> {output_path}")

    try:
        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download with urllib (no external dependencies)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.0"
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
        return True

    except urllib.error.HTTPError as e:
        print(f"     ❌ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"     ❌ URL Error: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"     ❌ Error: {e}", file=sys.stderr)
        return False


def download_episodes(
    podcast: Podcast,
    indices: list,
    output_dir: Path,
    template: str
) -> tuple:
    """
    Download multiple episodes by indices.

    Returns (success_count, failure_count).
    """
    success = 0
    failure = 0

    print(f"\n📥 Downloading from: {podcast.title}")
    print(f"   Output directory: {output_dir}")
    print("-" * 80)

    for idx in indices:
        episode = podcast.get_episode(idx)
        if not episode:
            print(f"  ⚠️  Episode {idx} not found", file=sys.stderr)
            failure += 1
            continue

        if download_episode(episode, podcast.title, idx, output_dir, template):
            success += 1
        else:
            failure += 1

    print("-" * 80)
    print(f"   Complete: {success} succeeded, {failure} failed")

    return success, failure


def parse_episode_indices(episode_str: str) -> list:
    """
    Parse episode index string into list of integers.

    Supports: "1", "1,3,5", "1-5", "1,3-5,7"
    """
    indices = set()

    for part in episode_str.split(','):
        part = part.strip()
        if '-' in part:
            # Range: "1-5"
            start, end = part.split('-', 1)
            indices.update(range(int(start), int(end) + 1))
        else:
            # Single: "1"
            indices.add(int(part))

    return sorted(indices)


def main():
    parser = argparse.ArgumentParser(
        description="Download podcast episodes from 小宇宙, Apple Podcasts, and RSS feeds"
    )
    parser.add_argument("url", help="Podcast URL (小宇宙, Apple Podcasts, or RSS feed)")

    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--list", action="store_true", help="List episodes without downloading")
    action_group.add_argument("--latest", action="store_true", help="Download the latest episode(s)")
    action_group.add_argument("--episode", type=str, metavar="N", help="Download specific episode(s) by index (1,3,5 or 1-5)")
    action_group.add_argument("--all", action="store_true", help="Download all episodes")

    # Options
    parser.add_argument("--limit", type=int, metavar="N", help="Limit number of episodes (for --list or --latest)")
    parser.add_argument("--output", type=Path, default=Path.home() / "Downloads" / "Podcasts", help="Output directory")
    parser.add_argument("--template", type=str, default="{date}_{title}.{ext}", help="Filename template")

    args = parser.parse_args()

    try:
        # Step 1: Detect platform and fetch podcast data
        print(f"🔍 Detecting platform...")
        podcast = get_podcast_from_url(args.url)
        print(f"📡 Found: {podcast.title} ({len(podcast.episodes)} episodes)")

        # Step 3: Execute action
        if args.list:
            list_episodes(podcast, args.limit)
            return 0

        # Download actions
        if args.latest:
            limit = args.limit or 1
            indices = list(range(1, min(limit + 1, len(podcast.episodes) + 1)))
        elif args.episode:
            indices = parse_episode_indices(args.episode)
        elif args.all:
            indices = list(range(1, len(podcast.episodes) + 1))
        else:
            print("Error: No action specified", file=sys.stderr)
            return 1

        success, failure = download_episodes(podcast, indices, args.output, args.template)
        return 0 if failure == 0 else 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
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
