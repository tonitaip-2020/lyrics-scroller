#!/usr/bin/env python3
"""
Merge per-song lyrics CSVs into a single SRT, offset by album start times.

Inputs expected in one folder:
  - starts.txt           (lines like: "01 00:00:00" with base-32 frames in the last field)
  - 01-lyrics-aligned.csv ... 09-lyrics-aligned.csv
Each CSV row: start_seconds, 0, lyric_text (quoted iff containing commas). Lyric text may be empty.

Rules for SRT end times:
  - Each line ends 0.01s before the next line's start, but at most 3 seconds after its own start.
  - For the final line, or if spacing < 0.01s, enforce a minimal duration of 0.01s.
  - Album offsets are applied from starts.txt (minutes:seconds:frames@32fps).

Usage:
  python merge_lyrics_to_srt.py /path/to/folder output.srt
"""

import csv
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

FPS = 32  # base-32 frames per "split-seconds"
MAX_DURATION = 4.0
GAP = 0.01  # 1/100 of a second
MIN_DURATION = 0.01  # ensure end > start for SRT

def parse_timecode_base32(tc: str) -> float:
    """
    Parse a timecode of form MM:SS:FF where FF are frames at 32 fps.
    Returns seconds as float.
    """
    m = re.fullmatch(r"(\d+):(\d+):(\d+)", tc.strip())
    if not m:
        raise ValueError(f"Bad timecode '{tc}' (expected MM:SS:FF base-32)")
    mm, ss, ff = map(int, m.groups())
    return mm * 60.0 + ss + (ff / FPS)

def s_to_srt_ts(t: float) -> str:
    """
    Convert seconds (float) to SRT timestamp "HH:MM:SS,mmm".
    """
    if t < 0:
        t = 0.0
    ms_total = int(round(t * 1000.0))
    hh = ms_total // 3_600_000
    rem = ms_total % 3_600_000
    mm = rem // 60_000
    rem = rem % 60_000
    ss = rem // 1000
    ms = rem % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"

def read_starts(starts_path: Path) -> List[Tuple[str, float]]:
    """
    Read starts.txt lines like '01 00:00:00' and return list of (track_no_str, offset_seconds).
    """
    starts = []
    with starts_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"Bad line in starts.txt: {line}")
            track_no, tc = parts
            offset = parse_timecode_base32(tc)
            starts.append((track_no, offset))
    # Sort by track number as string with zero padding (e.g., '01'...'09')
    starts.sort(key=lambda x: x[0])
    return starts

def read_lyrics_csv(csv_path: Path) -> List[Tuple[float, str]]:
    """
    Return list of (start_seconds, text). Column 2 is ignored (always '0').
    Preserve empty lyrics lines as empty strings.
    """
    rows: List[Tuple[float, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader, start=1):
            if not row:
                continue
            # Expect at least two columns; third (text) may be missing if empty
            try:
                start = float(row[0].strip())
            except Exception as e:
                raise ValueError(f"{csv_path.name}: line {i}: invalid start time: {row!r}") from e
            text = ""
            if len(row) >= 3:
                text = row[2]
            # Normalize None -> ""
            text = "" if text is None else text
            rows.append((start, text))
    # Ensure sorted by start
    rows.sort(key=lambda x: x[0])
    return rows

def collect_all_entries(folder: Path) -> List[Tuple[float, str]]:
    """
    Gather entries across all 9 CSVs with album offsets applied.
    Returns list of (album_start_seconds, text), sorted by time.
    """
    starts = read_starts(folder / "starts.txt")
    entries: List[Tuple[float, str]] = []

    for track_no, album_offset in starts:
        fname = f"{track_no}-lyrics-aligned.csv"
        fpath = folder / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing file: {fname}")
        rows = read_lyrics_csv(fpath)
        for local_start, text in rows:
            album_time = album_offset + local_start
            entries.append((album_time, text))

    # Sort globally by album_time
    entries.sort(key=lambda x: x[0])
    return entries

def compute_intervals(entries: List[Tuple[float, str]]) -> List[Tuple[float, float, str]]:
    """
    From a sorted list of (start, text), compute (start, end, text)
    using the rules:
      end = min(start + 3.0, next_start - 0.01)
      minimal duration enforced = 0.01s
    For the last entry: end = start + 3.0
    """
    result: List[Tuple[float, float, str]] = []
    n = len(entries)
    for i, (start, text) in enumerate(entries):
        if i < n - 1:
            next_start = entries[i + 1][0]
            end = min(start + MAX_DURATION, next_start - GAP)
        else:
            end = start + MAX_DURATION
        if end <= start:
            end = start + MIN_DURATION
        result.append((start, end, text))
    return result

def write_srt(intervals: List[Tuple[float, float, str]], out_path: Path) -> None:
    """
    Write SRT file with sequential indices.
    Include even empty-text cues to preserve timing (renders as a blank line on screen).
    """
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        for idx, (start, end, text) in enumerate(intervals, start=1):
            out.write(f"{idx}\n")
            out.write(f"{s_to_srt_ts(start)} --> {s_to_srt_ts(end)}\n")
            # Write text as-is. If empty, leave it blank to clear any prior subtitle.
            out.write(f"{text}\n\n")

def main():
    if len(sys.argv) != 3:
        print("Usage: python merge_lyrics_to_srt.py <input_folder> <output_file.srt>", file=sys.stderr)
        sys.exit(1)

    in_dir = Path(sys.argv[1]).expanduser().resolve()
    out_file = Path(sys.argv[2]).expanduser().resolve()

    if not in_dir.exists() or not in_dir.is_dir():
        print(f"Input folder not found: {in_dir}", file=sys.stderr)
        sys.exit(2)

    starts_file = in_dir / "starts.txt"
    if not starts_file.exists():
        print(f"starts.txt not found in folder: {in_dir}", file=sys.stderr)
        sys.exit(3)

    entries = collect_all_entries(in_dir)
    intervals = compute_intervals(entries)
    write_srt(intervals, out_file)
    print(f"Wrote {out_file} with {len(intervals)} cues.")

if __name__ == "__main__":
    main()
