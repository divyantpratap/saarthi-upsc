#!/bin/bash
# Downloads freely redistributable UPSC source material into the local corpus.
# Nothing here is committed: only the derived index ships. The directory name
# carries "ncert" so ingest/tiers.py classifies these as Tier A (quotable).
set -uo pipefail
DEST="data/pdfs/ncert"
PRUNE=false
if [ "${1:-}" = "--prune" ]; then
  PRUNE=true
elif [ -n "${1:-}" ]; then
  echo "usage: bash ingest/fetch_open_corpus.sh [--prune]" >&2
  exit 2
fi

mkdir -p "$DEST"
expected=$(mktemp)
trap 'rm -f "$expected"' EXIT
total=0
while IFS='|' read -r code subject title; do
  [ -z "${code:-}" ] && continue
  slug=$(echo "$title" | tr ' /—' '_' | tr -cd 'A-Za-z0-9_-')
  out="$DEST/${subject}_${slug}"
  echo "$out" >> "$expected"
  if [ -d "$out" ] && [ -n "$(ls -A "$out" 2>/dev/null)" ]; then
    echo "  have    $title"; continue
  fi
  mkdir -p "$out"
  if curl -sfL --max-time 180 "https://ncert.nic.in/textbook/pdf/${code}.zip" -o "$out/book.zip"; then
    if unzip -qo "$out/book.zip" -d "$out" 2>/dev/null; then
      rm -f "$out/book.zip"
      n=$(find "$out" -name '*.pdf' | wc -l | tr -d ' ')
      sz=$(du -sm "$out" | cut -f1)
      total=$((total+sz))
      echo "  ok      $title  (${n} PDFs, ${sz}MB)"
    else
      echo "  UNZIP FAILED  $title"; rm -rf "$out"
    fi
  else
    echo "  DOWNLOAD FAILED  $title"; rm -rf "$out"
  fi
done < ingest/ncert_books.txt

# A corrected manifest can leave an old, wrongly labelled directory behind.
# Do not let it silently join the next public index. Default to a loud warning;
# --prune moves it outside PDF_DIR so the operation stays recoverable.
stale=0
for directory in "$DEST"/*; do
  [ -d "$directory" ] || continue
  if ! grep -Fqx "$directory" "$expected"; then
    if [ "$PRUNE" = true ]; then
      quarantine="data/quarantine/ncert-$(date +%Y%m%d-%H%M%S)"
      mkdir -p "$quarantine"
      mv "$directory" "$quarantine/"
      echo "  moved   $directory -> $quarantine/"
    else
      echo "  STALE   $directory" >&2
      stale=1
    fi
  fi
done

if [ "$stale" -ne 0 ]; then
  echo "stale NCERT directories remain; re-run with --prune to move them to data/quarantine/" >&2
  exit 2
fi

echo "total ${total}MB in $DEST"
find "$DEST" -name '*.pdf' | wc -l | xargs echo "total PDFs:"
