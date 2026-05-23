#!/bin/bash
# RH wrapper — runs command, shows output, forces clipboard copy
OUTFILE=$(mktemp /tmp/rh_out.XXXXXX)
{
  echo "════════════════════════════════════════════════════════"
  echo "🎯 RH Run — $(TZ=America/Lima date +%H:%M:%S) Peru"
  echo "════════════════════════════════════════════════════════"
  eval "$@"
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "✅ Done — $(TZ=America/Lima date +%H:%M:%S) Peru"
  echo "════════════════════════════════════════════════════════"
} 2>&1 | tee "$OUTFILE"
cat "$OUTFILE" | pbcopy
echo ""
echo "📋📋📋 הפלט הועתק ל-clipboard ($(wc -l < "$OUTFILE") שורות) — Cmd+V בצ'אט 📋📋📋"
