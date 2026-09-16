#!/usr/bin/env python3
"""Fail when a tracked media file is not committed through Git LFS."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MEDIA_SUFFIXES = {
    ".aac",
    ".avi",
    ".avif",
    ".bmp",
    ".flac",
    ".gif",
    ".heic",
    ".heif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".oga",
    ".ogg",
    ".pdf",
    ".png",
    ".psd",
    ".svg",
    ".tif",
    ".tiff",
    ".wav",
    ".webm",
    ".webp",
}
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def tracked_media() -> list[str]:
    paths = git("ls-files", "-z").decode("utf-8").split("\0")
    return sorted(
        path
        for path in paths
        if path and Path(path).suffix.lower() in MEDIA_SUFFIXES
    )


def lfs_attribute(path: str) -> str:
    fields = git("check-attr", "--cached", "-z", "filter", "--", path).split(
        b"\0"
    )
    return fields[2].decode("utf-8")


def main() -> int:
    media = tracked_media()
    failures: list[str] = []

    for path in media:
        if lfs_attribute(path) != "lfs":
            failures.append(f"{path}: missing 'filter=lfs' attribute")
            continue

        blob = git("cat-file", "-p", f"HEAD:{path}")
        if not blob.startswith(LFS_POINTER_PREFIX):
            failures.append(f"{path}: Git blob is not an LFS pointer")

    if failures:
        print("Tracked media must be stored with Git LFS:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Verified {len(media)} tracked media file(s) use Git LFS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
