#!/data/data/com.termux/files/usr/bin/bash
# ═══════════════════════════════════════════════════════════════
#  zesChrome Extension Packager
#  Creates a zip + unpacked folder for Kiwi/Quetta/Chrome
# ═══════════════════════════════════════════════════════════════

set -e

EXT_SRC="$HOME/Zes-System/zes-chrome"
OUT_DIR="/storage/emulated/0/Download"
ZIP_NAME="zes-chrome-v1.0.0.zip"

echo "🔨 zesChrome Extension Packager"
echo "══════════════════════════════════"

[ -d "$EXT_SRC" ] || { echo "❌ Extension not found"; exit 1; }
echo "✅ Source: $EXT_SRC"

# Generate icons
echo "🎨 Generating icons..."
cd "$EXT_SRC/icons"

cat > icon16.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#03a9f4"/><stop offset="100%" style="stop-color:#f441a5"/>
  </linearGradient></defs>
  <rect width="16" height="16" rx="3" fill="#0f172a"/>
  <text x="8" y="12" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="11" fill="url(#g)">Z</text>
</svg>
SVGEOF

cat > icon48.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#03b9f4"/><stop offset="100%" style="stop-color:#f441a5"/>
  </linearGradient></defs>
  <rect width="48" height="48" rx="8" fill="#0f172a"/>
  <text x="24" y="34" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="28" fill="url(#g)">Z</text>
</svg>
SVGEOF

cat > icon128.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#03b9f4"/><stop offset="100%" style="stop-color:#f441a5"/>
  </linearGradient></defs>
  <rect width="128" height="128" rx="16" fill="#0f172a"/>
  <text x="64" y="88" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="72" fill="url(#g)">Z</text>
</svg>
SVGEOF

# Convert SVG to PNG
if command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 16 -h 16 icon16.svg -o icon16.png 2>/dev/null
    rsvg-convert -w 48 -h 48 icon48.svg -o icon48.png 2>/dev/null
    rsvg-convert -w 128 -h 128 icon128.svg -o icon128.png 2>/dev/null
    echo "  ✅ Icons via rsvg-convert"
else
    python3 -c "
import struct, zlib
def png(w, h, fn):
    raw = b''
    for y in range(h):
        raw += b'\x00'
        for x in range(w):
            r = int(3 + (x/w)*244) if y < h//4 or y >= h*3//4 or abs(x-y-h//2) < max(2,w//8) else 15
            g = int(169 - (x/w)*128) if y < h//4 or y >= h*3//4 or abs(x-y-h//2) < max(2,w//8) else 23
            b = int(244 - (y/h)*100) if y < h//4 or y >= h*3//4 or abs(x-y-h//2) < max(2,w//8) else 42
            raw += struct.pack('BBB', r, g, b)
    raw = zlib.compress(raw)
    with open(fn, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        for ctype, data in [(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)),
                            (b'IDAT', raw), (b'IEND', b'')]:
            c = ctype + data
            f.write(struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff))
png(16, 16, 'icon16.png'); png(48, 48, 'icon48.png'); png(128, 128, 'icon128.png')
print('  ✅ Icons via Python PNG')
"
fi

# Package
echo "📦 Creating zip..."
cd "$EXT_SRC"
rm -f "$OUT_DIR/$ZIP_NAME" 2>/dev/null

zip -r "$OUT_DIR/$ZIP_NAME" \
    manifest.json background.js content.js \
    popup.html popup.js popup.css \
    sidepanel.html sidepanel.js sidepanel.css \
    icons/icon16.png icons/icon48.png icons/icon128.png \
    lib/api-client.js \
    -x "*.svg" 2>/dev/null

echo "  ✅ Zip: $OUT_DIR/$ZIP_NAME ($(du -h "$OUT_DIR/$ZIP_NAME" | cut -f1))"

# Unpacked copy for developer mode
UNPACKED_DIR="$OUT_DIR/zes-chrome"
rm -rf "$UNPACKED_DIR"
mkdir -p "$UNPACKED_DIR"
# Copy selectively (ignore SVG, mcp-server, etc.)
for f in manifest.json background.js content.js popup.html popup.js popup.css sidepanel.html sidepanel.js sidepanel.css; do
    cp "$EXT_SRC/$f" "$UNPACKED_DIR/" 2>/dev/null || true
done
mkdir -p "$UNPACKED_DIR/icons" "$UNPACKED_DIR/lib"
cp "$EXT_SRC/icons/icon16.png" "$EXT_SRC/icons/icon48.png" "$EXT_SRC/icons/icon128.png" "$UNPACKED_DIR/icons/" 2>/dev/null
cp "$EXT_SRC/lib/api-client.js" "$UNPACKED_DIR/lib/" 2>/dev/null || true
echo "  ✅ Unpacked: $UNPACKED_DIR"

echo ""
echo "════════════════════════════════════════════════════"
echo "  zesChrome Extension Packaged!                     "
echo "════════════════════════════════════════════════════"
echo ""
echo "  📦 Zip:     $OUT_DIR/$ZIP_NAME"
echo "  📂 Unpacked: $UNPACKED_DIR"
echo ""
echo "  📲 Kiwi Browser:"
echo "     → Open kiwi://extensions (or chrome://extensions)"
echo "     → Enable Developer mode"
echo "     → 'Load unpacked' → select:"
echo "       $UNPACKED_DIR"
echo ""
echo "  📲 Quetta Browser:"
echo "     → Open quetta://extensions"
echo "     → Enable Developer mode → 'Load unpacked'"
echo "     → Select: $UNPACKED_DIR"
echo ""
echo "  ✅ After loading: extension badge shows Z"
echo "  ✅ Side panel accessible via Ctrl+Shift+S"
echo "  ✅ Connects to dashboard at :8083"
echo "════════════════════════════════════════════════════"
