#!/usr/bin/env bash
# Cut one segment out of a source video, at sentence boundaries, with audio fades.
# usage: cut_clip.sh <source.mp4> <start_s> <end_s> <out.mp4>
# env:   PAD_IN=0.15  PAD_OUT=0.35  FADE_IN=0.15  FADE_OUT=0.30  CRF=18
set -euo pipefail

SRC="$1"; START="$2"; END="$3"; OUT="$4"
PAD_IN="${PAD_IN:-0.15}"; PAD_OUT="${PAD_OUT:-0.35}"; FADE_IN="${FADE_IN:-0.15}"; FADE_OUT="${FADE_OUT:-0.30}"; CRF="${CRF:-18}"

START=$(python3 -c "print(max(0, round($START - $PAD_IN, 3)))")
END_PAD=$(python3 -c "print(round($END + $PAD_OUT, 3))")
DUR=$(python3 -c "print(round($END_PAD - $START, 3))")
FADE_OUT_ST=$(python3 -c "print(max(0, round($DUR - $FADE_OUT, 3)))")

mkdir -p "$(dirname "$OUT")"
ffmpeg -y -loglevel error -ss "$START" -to "$END_PAD" -i "$SRC" \
  -af "afade=t=in:st=0:d=${FADE_IN},afade=t=out:st=${FADE_OUT_ST}:d=${FADE_OUT}" \
  -c:v libx264 -crf "$CRF" -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"

REAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
level() { ffmpeg -loglevel info -ss "$1" -t 0.3 -i "$OUT" -af volumedetect -f null - 2>&1 \
          | awk -F': ' '/mean_volume/{print $2}'; }
HEAD=$(level 0)
TAIL=$(level "$(python3 -c "print(max(0, $REAL - 0.3))")")

printf '%s\n' "$OUT" "  src ${START}s → ${END_PAD}s (pad in ${PAD_IN}s / out ${PAD_OUT}s)  duration ${REAL}s" \
  "  head 0.3s: ${HEAD:-n/a}   tail 0.3s: ${TAIL:-n/a}   (tail target ≤ -40 dB; head is masked by the fade-in)"
