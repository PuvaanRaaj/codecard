#!/bin/bash
# Shared warm/filmic grade recipe for this project's footage.
# Usage: grade.sh <crop_filter_or_empty> <input> <output> [extra_vf]
# crop_filter_or_empty: an ffmpeg crop=... filter fragment (or empty string to skip)
set -euo pipefail
CROP="$1"
IN="$2"
OUT="$3"
EXTRA="${4:-}"

GRADE="eq=contrast=1.08:saturation=0.96:brightness=0.0,colorbalance=rs=-0.09:gs=0.02:bs=0.11:rm=0.02:gm=0.0:bm=0.02:rh=0.09:gh=0.0:bh=-0.06,curves=r='0/0.02 0.5/0.51 1/0.97':b='0/0.02 0.5/0.48 1/0.9',vignette=PI/3.2,noise=alls=14:allf=t+u"
PILLARBOX="pad=1920:1080:(1920-1440)/2:0:color=black"

if [ -n "$CROP" ]; then
  VF="${CROP},${GRADE},${PILLARBOX}"
else
  VF="${GRADE},${PILLARBOX}"
fi
if [ -n "$EXTRA" ]; then
  VF="${VF},${EXTRA}"
fi

ffmpeg -y -v error -i "$IN" -vf "$VF" -an -c:v libx264 -crf 16 -pix_fmt yuv420p "$OUT"
echo "wrote $OUT"
