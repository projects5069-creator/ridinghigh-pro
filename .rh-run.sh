#!/bin/bash
# RH wrapper — runs command, shows output, forces FULL clipboard copy
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

# Force FULL copy: entire file -> clipboard, byte-exact
pbcopy < "$OUTFILE"

LINES=$(wc -l < "$OUTFILE" | tr -d ' ')
CHARS=$(wc -c < "$OUTFILE" | tr -d ' ')
CLIP=$(pbpaste | wc -c | tr -d ' ')
echo ""
echo "📋 הועתק ל-clipboard: ${LINES} שורות · ${CHARS} תווים"
if [ "$CHARS" = "$CLIP" ]; then
  echo "✅ אימות: clipboard מכיל ${CLIP} תווים — תואם במדויק. Cmd+V ישיר בצ'אט (בלי לסמן)."
else
  echo "⚠️ אי-התאמה: קובץ ${CHARS} ≠ clipboard ${CLIP} — pbcopy נכשל, דווח לי."
fi
