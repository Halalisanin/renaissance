#!/usr/bin/env bash
set -eu

source_dir="${1:-assets/direct_book/PDF}"
target_dir="${2:-assets/direct_book/thumbnails}"
mkdir -p "$target_dir"
for pdf in "$source_dir"/*.pdf "$source_dir"/*.PDF; do
  [ -f "$pdf" ] || continue
  name="$(basename "$pdf")"
  name="${name%.*}"
  pdftoppm -f 1 -l 1 -singlefile -jpeg -scale-to 900 "$pdf" "$target_dir/$name"
done