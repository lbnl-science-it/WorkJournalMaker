# ABOUTME: Generates placeholder app icons for macOS (.icns) and Windows (.ico) formats.
# ABOUTME: Creates a simple colored PNG with border, then converts to platform-specific formats.
"""Generate placeholder app icons for macOS and Windows."""
import struct
import zlib
import os


def create_png(width, height, color_rgb, text_color_rgb, output_path):
    """Create a simple colored PNG with a border pattern."""
    pixels = []
    border = width // 10
    for y in range(height):
        row = []
        for x in range(width):
            if x < border or x >= width - border or y < border or y >= height - border:
                row.extend(text_color_rgb)
                row.append(255)
            else:
                row.extend(color_rgb)
                row.append(255)
        pixels.append(bytes([0] + row))  # filter byte + RGBA

    raw = b''.join(pixels)

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))


def create_ico(png_path, ico_path):
    """Create a minimal .ico from a PNG file."""
    with open(png_path, 'rb') as f:
        png_data = f.read()

    header = struct.pack('<HHH', 0, 1, 1)
    entry = struct.pack('<BBBBHHIH', 0, 0, 0, 0, 1, 32, len(png_data), 22)

    with open(ico_path, 'wb') as f:
        f.write(header + entry + png_data)


if __name__ == '__main__':
    blue = [41, 98, 255]
    white = [255, 255, 255]

    os.makedirs('assets', exist_ok=True)

    create_png(1024, 1024, blue, white, 'assets/icon_source.png')
    create_png(256, 256, blue, white, 'assets/icon_256.png')

    create_ico('assets/icon_256.png', 'assets/icon.ico')

    print("Generated: assets/icon_source.png, assets/icon_256.png, assets/icon.ico")
    print("NOTE: For macOS .icns, run on macOS:")
    print("  mkdir icon.iconset")
    print("  sips -z 1024 1024 assets/icon_source.png --out icon.iconset/icon_512x512@2x.png")
    print("  sips -z 512 512 assets/icon_source.png --out icon.iconset/icon_512x512.png")
    print("  sips -z 256 256 assets/icon_source.png --out icon.iconset/icon_256x256.png")
    print("  sips -z 128 128 assets/icon_source.png --out icon.iconset/icon_128x128.png")
    print("  sips -z 64 64 assets/icon_source.png --out icon.iconset/icon_64x64.png")
    print("  sips -z 32 32 assets/icon_source.png --out icon.iconset/icon_32x32.png")
    print("  sips -z 16 16 assets/icon_source.png --out icon.iconset/icon_16x16.png")
    print("  iconutil -c icns icon.iconset -o assets/icon.icns")
    print("  rm -rf icon.iconset")
