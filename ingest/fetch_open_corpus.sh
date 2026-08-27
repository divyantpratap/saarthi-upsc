#!/bin/bash
# Downloads freely redistributable UPSC source material into the local corpus.
# Nothing here is committed: only the derived index ships. The directory name
# carries "ncert" so ingest/tiers.py classifies these as Tier A (quotable).
set -uo pipefail
DEST="data/pdfs/ncert"
mkdir -p "$DEST"
total=0
while IFS='|' read -r code subject title; do
  [ -z "${code:-}" ] && continue
  slug=$(echo "$title" | tr ' /—' '_' | tr -cd 'A-Za-z0-9_-')
  out="$DEST/${subject}_${slug}"
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
echo "total ${total}MB in $DEST"
find "$DEST" -name '*.pdf' | wc -l | xargs echo "total PDFs:"
