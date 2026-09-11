#!/usr/bin/env python3
"""Flatten a YouTube json3 subtitle track into word- and sentence-level timings.

usage: json3_to_words.py track.json3 [--gap 0.7] > words.json

Output: {"words": [{text,start,end}], "sentences": [{text,start,end}]}
Times are seconds. Sentences split on terminal punctuation (.!?…) or a pause > --gap.
"""
import json
import re
import sys

TERMINAL = re.compile(r"[.!?…]['\"»)]*$")
TAG = re.compile(r"^\[.*\]$")  # [musique], [Music], [Applause]…


def load_words(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    words = []
    for ev in data.get("events", []):
        if ev.get("aAppend") or "segs" not in ev:
            continue
        base = ev.get("tStartMs", 0)
        ev_end = base + ev.get("dDurationMs", 0)
        segs = [s for s in ev["segs"] if s.get("utf8", "").strip() and not TAG.match(s["utf8"].strip())]
        for i, s in enumerate(segs):
            start = base + s.get("tOffsetMs", 0)
            if i + 1 < len(segs):
                end = base + segs[i + 1].get("tOffsetMs", 0)
            else:
                end = ev_end
            words.append({"text": s["utf8"].strip(), "start": start / 1000, "end": end / 1000})
    # fix overlaps: a word never ends after the next one starts
    for i in range(len(words) - 1):
        if words[i]["end"] > words[i + 1]["start"]:
            words[i]["end"] = words[i + 1]["start"]
    return words


def group_sentences(words, gap):
    sentences, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = (nxt["start"] - w["end"]) if nxt else 999
        if TERMINAL.search(w["text"]) or pause > gap or nxt is None:
            sentences.append({
                "text": " ".join(x["text"] for x in cur),
                "start": round(cur[0]["start"], 3),
                "end": round(cur[-1]["end"], 3),
            })
            cur = []
    return sentences


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    gap = 0.7
    if "--gap" in args:
        i = args.index("--gap")
        gap = float(args[i + 1])
        del args[i:i + 2]
    words = load_words(args[0])
    for w in words:
        w["start"], w["end"] = round(w["start"], 3), round(w["end"], 3)
    out = {"words": words, "sentences": group_sentences(words, gap)}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
