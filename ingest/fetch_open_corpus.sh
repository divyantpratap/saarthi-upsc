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
stale=0
quarantine="data/quarantine/ncert-$(date +%Y%m%d-%H%M%S)"
while IFS='|' read -r code subject title; do
  [ -z "${code:-}" ] && continue
  # Include the NCERT code in the directory name: it is the stable identity.
  # Byte-oriented tr makes this deterministic across macOS/Linux locales.
  slug=$(printf '%s' "$title" | LC_ALL=C tr -cs 'A-Za-z0-9' '_' | sed 's/^_//; s/_$//')
  out="$DEST/${code}_${subject}_${slug}"
  echo "$out" >> "$expected"
  prefix=${code%dd}

  if [ -d "$out" ] && [ -n "$(ls -A "$out" 2>/dev/null)" ]; then
    pdf_count=$(find "$out" -type f -name '*.pdf' | wc -l | tr -d ' ')
    matching_count=$(find "$out" -type f -name "${prefix}*.pdf" | wc -l | tr -d ' ')
    if [ "$pdf_count" -gt 0 ] && [ "$pdf_count" -eq "$matching_count" ]; then
      echo "  have    $title"; continue
    fi

    if [ "$PRUNE" = true ]; then
      mkdir -p "$quarantine"
      mv "$out" "$quarantine/"
      echo "  moved   mismatched $out -> $quarantine/"
    else
      echo "  WRONG   $out does not contain ${prefix}*.pdf" >&2
      stale=1
      continue
    fi
  fi

  # Reuse a correctly downloaded book filed under an older/wrong title. This
  # is a metadata move only; no PDF is deleted and no network call is needed.
  candidate=""
  for directory in "$DEST"/*; do
    [ -d "$directory" ] || continue
    [ "$directory" = "$out" ] && continue
    pdf_count=$(find "$directory" -type f -name '*.pdf' | wc -l | tr -d ' ')
    matching_count=$(find "$directory" -type f -name "${prefix}*.pdf" | wc -l | tr -d ' ')
    if [ "$pdf_count" -gt 0 ] && [ "$pdf_count" -eq "$matching_count" ]; then
      candidate="$directory"
      break
    fi
  done
  if [ -n "$candidate" ]; then
    if [ "$PRUNE" = true ]; then
      mv "$candidate" "$out"
      echo "  relabel $candidate -> $out"
      continue
    fi
    echo "  MIGRATE $candidate -> $out" >&2
    stale=1
    continue
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
for directory in "$DEST"/*; do
  [ -d "$directory" ] || continue
  if ! grep -Fqx "$directory" "$expected"; then
    if [ "$PRUNE" = true ]; then
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
