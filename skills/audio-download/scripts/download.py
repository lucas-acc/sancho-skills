#!/usr/bin/env python3
"""
Audio download helper script using yt-dlp.
Supports YouTube and Twitter/X URLs.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """Check if URL is a supported platform (YouTube or Twitter/X)."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # YouTube domains
    youtube_domains = [
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com",
        "music.youtube.com",
    ]

    # Twitter/X domains
    twitter_domains = [
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "www.x.com",
        "mobile.twitter.com",
        "mobile.x.com",
    ]

    all_supported = youtube_domains + twitter_domains
    return any(domain.endswith(d) or domain == d for d in all_supported)


def get_platform(url: str) -> str:
    """Identify the platform from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    youtube_domains = ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"]
    if any(domain.endswith(d) or domain == d for d in youtube_domains):
        return "YouTube"

    twitter_domains = ["twitter.com", "www.twitter.com", "x.com", "www.x.com"]
    if any(domain.endswith(d) or domain == d for d in twitter_domains):
        return "Twitter/X"

    return "Unknown"


def build_ytdlp_command(
    url: str,
    output_dir: Path,
    audio_format: str,
    audio_quality: str,
    playlist_items: int | None = None,
    embed_metadata: bool = True,
) -> list[str]:
    """Build yt-dlp command with specified options."""

    # Map quality strings to yt-dlp values
    quality_map = {
        "best": "0",
        "worst": "9",
    }
    quality = quality_map.get(audio_quality, audio_quality)

    # Build output template
    output_template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",  # Extract audio
        "--audio-format", audio_format,
        "--audio-quality", quality,
        "-o", output_template,
    ]

    if embed_metadata:
        cmd.extend(["--embed-metadata"])

    if playlist_items is not None:
        cmd.extend(["--playlist-items", f"1:{playlist_items}"])

    cmd.append(url)

    return cmd


def run_download(cmd: list[str]) -> bool:
    """Execute yt-dlp command and handle errors."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Download failed with exit code {e.returncode}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            "Error: yt-dlp not found. Please install it:\n"
            "  brew install yt-dlp\n"
            "  or\n"
            "  pip install yt-dlp",
            file=sys.stderr,
        )
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download audio from YouTube and Twitter/X links"
    )
    parser.add_argument("url", help="URL to download audio from")
    parser.add_argument(
        "--format",
        default="mp3",
        choices=["mp3", "m4a", "wav", "flac", "ogg"],
        help="Audio format (default: mp3)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "Downloads" / "audio",
        help="Output directory (default: ~/Downloads/audio)",
    )
    parser.add_argument(
        "--quality",
        default="0",
        help="Audio quality: 0 (best), 1-9, or 'worst' (default: 0)",
    )
    parser.add_argument(
        "--playlist-items",
        type=int,
        metavar="N",
        help="Download only first N items from playlists",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't embed metadata in output files",
    )

    args = parser.parse_args()

    # Validate URL
    if not validate_url(args.url):
        print(
            f"Error: Unsupported URL. Only YouTube and Twitter/X URLs are supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Identify platform
    platform = get_platform(args.url)
    print(f"Downloading from {platform}...")
    print(f"Output directory: {args.output}")
    print(f"Audio format: {args.format}")
    print()

    # Build and run command
    cmd = build_ytdlp_command(
        url=args.url,
        output_dir=args.output,
        audio_format=args.format,
        audio_quality=args.quality,
        playlist_items=args.playlist_items,
        embed_metadata=not args.no_metadata,
    )

    if run_download(cmd):
        print("\nDownload complete!")
        print(f"Files saved to: {args.output}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
