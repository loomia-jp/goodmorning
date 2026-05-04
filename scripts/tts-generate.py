#!/usr/bin/env python3
"""Generate an MP3 from a text script via OpenAI TTS.

Usage:
    python3 scripts/tts-generate.py \
        --input-file /tmp/brief.txt \
        --output-file /tmp/brief.mp3 \
        [--voice alloy] [--model gpt-4o-mini-tts]

Reads OPENAI_API_KEY from env. If unset, exits 0 silently without producing a
file (caller should treat missing output as "skip TTS"). The text input should
be a plain-text script (no Markdown / HTML).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

OPENAI_ENDPOINT = "https://api.openai.com/v1/audio/speech"
DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
# Cap input size so a runaway prompt cannot generate a 30+ minute audio file.
MAX_INPUT_CHARS = 6000


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MP3 from text via OpenAI TTS.")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--instructions", default=None,
                        help="Optional voice direction (e.g. 'speak slowly in Japanese')")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[tts-generate] OPENAI_API_KEY not set; skipping TTS.", file=sys.stderr)
        return 0

    in_path = pathlib.Path(args.input_file)
    if not in_path.exists():
        print(f"[tts-generate] ERROR: input not found: {in_path}", file=sys.stderr)
        return 1

    text = in_path.read_text(encoding="utf-8").strip()
    if not text:
        print("[tts-generate] input is empty; skipping.", file=sys.stderr)
        return 0
    if len(text) > MAX_INPUT_CHARS:
        print(
            f"[tts-generate] input is {len(text)} chars; truncating to {MAX_INPUT_CHARS}.",
            file=sys.stderr,
        )
        text = text[:MAX_INPUT_CHARS]

    payload = {
        "model": args.model,
        "voice": args.voice,
        "input": text,
        "format": "mp3",
    }
    if args.instructions:
        payload["instructions"] = args.instructions

    req = urllib.request.Request(
        OPENAI_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"[tts-generate] HTTP {e.code}: {detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"[tts-generate] network error: {e.reason}", file=sys.stderr)
        return 1

    out_path = pathlib.Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    size_kb = len(audio) / 1024
    print(f"[tts-generate] wrote {out_path} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
