#!/usr/bin/env python3
import argparse, subprocess, tempfile, os, time, sys
import simpleaudio as sa
from typing import List, Tuple

HELP = """Tap the start time for each lyric line while the song plays.
Controls:
  ENTER    -> mark current line
  u+ENTER  -> undo last
  p+ENTER  -> pause/resume (playback restarts from beginning; timer continues)
  q+ENTER  -> abort and save
"""

def load_lyrics(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        raise ValueError("No non-empty lines in lyrics file.")
    return lines

def transcode_to_wav(input_path: str, rate: int, channels: int) -> Tuple[str, float]:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    out = tmp.name
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-i", input_path, "-ar", str(rate), "-ac", str(channels),
           "-sample_fmt", "s16", out]
    subprocess.check_call(cmd)
    probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", out]
    dur = float(subprocess.check_output(probe).decode().strip())
    return out, dur

def load_waveobject(wav_path: str) -> sa.WaveObject:
    return sa.WaveObject.from_wave_file(wav_path)

def write_output(out_path: str, stamps: List[Tuple[float, str]], offset: float = 0.0) -> None:
    with open(out_path, "w", encoding="utf-8") as out:
        for t, line in stamps:
            t2 = max(0.0, t + offset)
            out.write(f'{t2:.3f},0,"{line.replace("\"","\\\"")}"\n')

def main():
    ap = argparse.ArgumentParser(description="Tap-in lyric line start times.",
                                 epilog=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="Audio file (mp3/wav/etc; ffmpeg required)")
    ap.add_argument("lyrics", help="Lyrics .txt (one line per line)")
    ap.add_argument("--out", default="aligned_lines.txt")
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--countdown", type=int, default=3)
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--channels", type=int, default=2)
    ap.add_argument("--autosave_every", type=int, default=0, help="Autosave after N taps (0=off)")
    args = ap.parse_args()

    wav_path = None
    play = None
    stamps: List[Tuple[float, str]] = []

    try:
        lines = load_lyrics(args.lyrics)
        wav_path, duration = transcode_to_wav(args.audio, args.rate, args.channels)
        wave_obj = load_waveobject(wav_path)

        print(f"Loaded: {args.audio} -> {wav_path} ({duration:.1f}s)")
        print(f"Lyrics: {len(lines)} lines -> {args.out}")

        if args.countdown > 0:
            for n in range(args.countdown, 0, -1):
                print(n, "…"); sys.stdout.flush(); time.sleep(1)
            print("Go!"); sys.stdout.flush()

        play = wave_obj.play()
        t0 = time.perf_counter()
        i, paused, pause_start, accumulated_pause = 0, False, None, 0.0
        autosave_every = max(0, args.autosave_every)

        def now() -> float:
            return time.perf_counter() - t0 - accumulated_pause

        while i < len(lines):
            print("\n---"); sys.stdout.flush()
            print(f'Line {i+1}/{len(lines)}: "{lines[i]}"'); sys.stdout.flush()
            print("ENTER mark | u undo | p pause/resume | q abort+save"); sys.stdout.flush()
            try:
                cmd = input().strip().lower()
            except EOFError:
                print("Input closed; saving current results…")
                break

            if cmd == "q":
                print("Aborting and saving partial results…")
                break

            if cmd == "u":
                if stamps:
                    t,l = stamps.pop(); i -= 1
                    print(f"Undid {t:.3f}s -> {l!r}")
                else:
                    print("Nothing to undo.")
                continue

            if cmd == "p":
                if not paused:
                    print("Pausing…")
                    if play and play.is_playing():
                        try: play.stop()
                        except Exception: pass
                    pause_start = time.perf_counter()
                    paused = True
                else:
                    print("Resuming…")
                    if pause_start is not None:
                        accumulated_pause += time.perf_counter() - pause_start
                    try:
                        play = wave_obj.play()  # restarts from beginning; timer continues
                    except Exception as e:
                        print(f"Warning: could not resume playback: {e}")
                    paused = False
                continue

            # Default: ENTER pressed → mark timestamp
            if paused:
                print("You are paused. Press p to resume, then tap."); continue

            t = now()
            stamps.append((t, lines[i]))
            print(f"Marked {t:.3f}s")
            i += 1

            # Optional autosave
            if autosave_every and (len(stamps) % autosave_every == 0):
                try:
                    write_output(args.out, stamps, offset=args.offset)
                    print(f"(Autosaved {len(stamps)} lines to {args.out})")
                except Exception as e:
                    print(f"(Autosave failed: {e})")

        # Stop playback (avoid wait_done hangs)
        if play and play.is_playing():
            try: play.stop()
            except Exception: pass

        write_output(args.out, stamps, offset=args.offset)
        print(f"\nSaved {len(stamps)} lines to {args.out}")

    except KeyboardInterrupt:
        print("\nInterrupted. Saving results…")
        if play and play.is_playing():
            try: play.stop()
            except Exception: pass
        try:
            write_output(args.out, stamps, offset=args.offset)
            print(f"Saved {len(stamps)} lines to {args.out}")
        except Exception as e:
            print(f"Failed to write output: {e}")
    finally:
        if wav_path and os.path.exists(wav_path):
            try: os.remove(wav_path)
            except Exception: pass

if __name__ == "__main__":
    main()
