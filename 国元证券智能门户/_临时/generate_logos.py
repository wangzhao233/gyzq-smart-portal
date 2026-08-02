"""
补全元信logo缺失文件：
1. wework.ico — 9种尺寸ICO（菜单栏通知）
2. wework_msg_normal.ico — 12种尺寸BMP ICO（托盘图标）
3. iOS 登录页logo — 93×99 PNG + PDF 带透明背景
4. 重命名 2048x2048 (1).png
"""

import os, struct, shutil
from PIL import Image

# ─── 配置 ───────────────────────────────────────────
SRC_ONLY_LOGO = r"C:/Users/11039/WorkBuddy/国元证券智能门户/_临时/logo_check/元信logo/元信logo/only_logo_2048x2048.png"
OUT_DIR = r"C:/Users/11039/WorkBuddy/国元证券智能门户/output/logo补全"
PC_OUT = r"C:/Users/11039/WorkBuddy/国元证券智能门户/_临时/logo_check/元信logo/元信logo/pc"

os.makedirs(OUT_DIR, exist_ok=True)

# ─── Helper: load source as RGBA ─────────────────────
def load_source(path):
    """Load image and convert to RGBA, preserving transparency."""
    img = Image.open(path)
    if img.mode == 'P':
        transparency = img.info.get('transparency')
        img = img.convert('RGBA')
    elif img.mode != 'RGBA':
        img = img.convert('RGBA')
    return img

# ─── Helper: resize with LANCZOS ─────────────────────
def resize_img(img, size):
    return img.resize(size, Image.LANCZOS)

# ─── ICO Builder (binary) ────────────────────────────
# ICO format: header(6) + dir_entries(16*N) + image_data

def build_ico_entry_bmp(img, width, height, bpp):
    """Build a BMP entry for ICO. Returns (entry_bytes, image_data_bytes)."""
    # img should be RGBA or RGB (for bpp=32) or P (for bpp=4,8)
    if bpp == 32:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
    elif bpp == 8:
        img = img.quantize(colors=256).convert('P')
    elif bpp == 4:
        img = img.quantize(colors=16).convert('P')
    
    w, h = img.size
    
    # XOR mask: BGR(A) pixel data, bottom-up, row padded to 4 bytes
    xor_rows = []
    if bpp == 32:
        for y in range(h-1, -1, -1):
            row = []
            for x in range(w):
                r, g, b, a = img.getpixel((x, y))
                row.extend([b, g, r, a])  # BGRA
            # Pad to 4-byte boundary
            while len(row) % 4:
                row.append(0)
            xor_rows.append(bytes(row))
    elif bpp == 8:
        palette = img.getpalette()
        for y in range(h-1, -1, -1):
            row = []
            for x in range(w):
                idx = img.getpixel((x, y))
                row.append(idx)
            while len(row) % 4:
                row.append(0)
            xor_rows.append(bytes(row))
    elif bpp == 4:
        palette = img.getpalette()
        for y in range(h-1, -1, -1):
            row = []
            for x in range(0, w, 2):
                idx1 = img.getpixel((x, y)) if x < w else 0
                idx2 = img.getpixel((x+1, y)) if x+1 < w else 0
                row.append((idx1 << 4) | (idx2 & 0x0F))
            while len(row) % 4:
                row.append(0)
            xor_rows.append(bytes(row))
    
    xor_data = b''.join(xor_rows)
    
    # AND mask: 1 bit per pixel, row padded to 4 bytes
    and_rows = []
    and_row_bytes = (w + 7) // 8
    padded_and_row = ((and_row_bytes + 3) // 4) * 4
    
    if bpp == 32 and img.mode == 'RGBA':
        # Use alpha channel: 0=transparent(AND=1), 255=opaque(AND=0)
        for y in range(h-1, -1, -1):
            row_bits = []
            for x in range(w):
                a = img.getpixel((x, y))[3]
                row_bits.append(0 if a > 127 else 1)
            row_bytes = bytearray(padded_and_row)
            for i, bit in enumerate(row_bits):
                if bit:
                    row_bytes[i // 8] |= (1 << (7 - (i % 8)))
            and_rows.append(bytes(row_bytes))
    else:
        # All opaque
        for y in range(h):
            and_rows.append(b'\x00' * padded_and_row)
    
    and_data = b''.join(and_rows)
    
    # BITMAPINFOHEADER (40 bytes)
    colors_used = 0
    if bpp == 4:
        colors_used = 16
    elif bpp == 8:
        colors_used = 256
    
    bih = struct.pack('<IiiHHIIiiII',
        40,            # biSize (BITMAPINFOHEADER is always 40 bytes)
        w,             # biWidth
        h * 2,         # biHeight (double for ICO: XOR+AND)
        1,             # biPlanes
        bpp,           # biBitCount
        0,             # biCompression
        len(xor_data) + len(and_data),  # biSizeImage
        0, 0, 0, 0     # biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant
    )
    
    # Palette data (if needed)
    palette_data = b''
    if bpp == 8 and palette:
        for i in range(256):
            palette_data += bytes(palette[i*3:i*3+3]) + b'\x00'  # BGR0
    elif bpp == 4 and palette:
        for i in range(16):
            palette_data += bytes(palette[i*3:i*3+3]) + b'\x00'
    
    image_data = bih + palette_data + xor_data + and_data
    
    # ICO directory entry
    w_byte = w if w < 256 else 0
    h_byte = h if h < 256 else 0
    # colors: 0 for 32bpp (no palette) or 256 (must be encoded as 0 in byte)
    color_byte = 0 if (bpp == 32 or colors_used >= 256) else colors_used
    entry = struct.pack('<BBBBHHII',
        w_byte, h_byte,      # width, height (0 = 256)
        color_byte,          # color count (0 = no palette / 256 colors)
        0,                   # reserved
        1,                   # planes
        bpp,                 # bpp
        len(image_data),     # size (bih + palette_data + xor_data + and_data combined)
        0                    # offset (filled later)
    )
    return entry, image_data


def build_ico_entry_png(img, width, height):
    """Build a PNG entry for ICO."""
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    png_data = buf.getvalue()
    
    w_byte = width if width < 256 else 0
    h_byte = height if height < 256 else 0
    
    entry = struct.pack('<BBBBHHII',
        w_byte, h_byte,  # width, height
        0,               # color count  
        0,               # reserved
        0,               # planes (0 = PNG)
        0,               # bpp (0 = PNG)
        len(png_data),   # size
        0                # offset
    )
    return entry, png_data


def save_ico(entries, output_path):
    """Save ICO file from list of (entry, data) tuples."""
    # Calculate offsets
    header_size = 6
    dir_size = 16 * len(entries)
    offset = header_size + dir_size
    
    # Rebuild entries with correct offsets
    updated_entries = []
    for entry, data in entries:
        # Patch offset into entry (last 4 bytes)
        updated_entry = entry[:12] + struct.pack('<I', offset)
        updated_entries.append((updated_entry, data))
        offset += len(data)
    
    # Write file
    with open(output_path, 'wb') as f:
        # Header
        f.write(struct.pack('<HHH', 0, 1, len(entries)))
        # Directory
        for entry, _ in updated_entries:
            f.write(entry)
        # Image data
        for _, data in updated_entries:
            f.write(data)
    
    print(f'  → {output_path} ({os.path.getsize(output_path)} bytes, {len(entries)} sizes)')


# ════════════════════════════════════════════════════
# 1. wework.ico — 9 sizes
# ════════════════════════════════════════════════════

print('生成 wework.ico ...')
src = load_source(SRC_ONLY_LOGO)

# wework sizes: BMP 16,32,40,48,64,128 (32-bit) + PNG 256,512,1024
wework_specs = [
    ('bmp', 16, 16, 32),
    ('bmp', 32, 32, 32),
    ('bmp', 40, 40, 32),
    ('bmp', 48, 48, 32),
    ('bmp', 64, 64, 32),
    ('bmp', 128, 128, 32),
    ('png', 256, 256, None),
    ('png', 512, 512, None),
    ('png', 1024, 1024, None),
]

entries = []
for fmt, w, h, bpp in wework_specs:
    img = resize_img(src, (w, h))
    if fmt == 'bmp':
        entry, data = build_ico_entry_bmp(img, w, h, bpp)
    else:
        entry, data = build_ico_entry_png(img, w, h)
    entries.append((entry, data))

save_ico(entries, os.path.join(OUT_DIR, 'wework.ico'))
# Also save to pc folder
save_ico(entries, os.path.join(PC_OUT, 'wework.ico'))


# ════════════════════════════════════════════════════
# 2. wework_msg_normal.ico — 12 sizes
# ════════════════════════════════════════════════════

print('\n生成 wework_msg_normal.ico ...')
src2 = load_source(SRC_ONLY_LOGO)

# 12 BMP entries with different bit depths
msg_normal_specs = [
    (16, 16, 4),    # 4-bit
    (32, 32, 4),    # 4-bit
    (16, 16, 8),    # 8-bit
    (32, 32, 8),    # 8-bit
    (48, 48, 8),    # 8-bit
    (16, 16, 32),   # 32-bit
    (20, 20, 32),   # 32-bit
    (24, 24, 32),   # 32-bit
    (32, 32, 32),   # 32-bit
    (40, 40, 32),   # 32-bit
    (48, 48, 32),   # 32-bit
    (64, 64, 32),   # 32-bit
]

entries2 = []
for w, h, bpp in msg_normal_specs:
    img = resize_img(src2, (w, h))
    entry, data = build_ico_entry_bmp(img, w, h, bpp)
    entries2.append((entry, data))

save_ico(entries2, os.path.join(OUT_DIR, 'wework_msg_normal.ico'))
save_ico(entries2, os.path.join(PC_OUT, 'wework_msg_normal.ico'))


# ════════════════════════════════════════════════════
# 3. iOS 登录页logo — 93×99 PNG + PDF 带透明
# ════════════════════════════════════════════════════

print('\n修复 iOS 登录页logo ...')
src3 = load_source(SRC_ONLY_LOGO)

# Step 1: Scale to 99×99 (maintain aspect ratio from square 2048×2048)
img_99 = resize_img(src3, (99, 99))

# Step 2: Center-crop to 93×99 (crop 3px from left and right)
left = (99 - 93) // 2   # 3
right = left + 93        # 96
top = 0
bottom = 99
img_93x99 = img_99.crop((left, top, right, bottom))
# Verify size
assert img_93x99.size == (93, 99), f"Unexpected size: {img_93x99.size}"

# Save PNG
ios_out = os.path.join(OUT_DIR, 'ios')
os.makedirs(ios_out, exist_ok=True)
png_path = os.path.join(ios_out, '登录页logo_93x99.png')
img_93x99.save(png_path, format='PNG')
print(f'  → {png_path} ({img_93x99.size[0]}×{img_93x99.size[1]}, mode={img_93x99.mode})')

# Save PDF (Pillow PDF is raster-embedded, not vector — acceptable per requirement "转换成pdf格式")
pdf_path = os.path.join(ios_out, '登录页logo_93x99.pdf')
# PDF: set page size to image size in points (1pt ≈ 1px at 72dpi)
img_93x99.save(pdf_path, format='PDF', resolution=72.0)
print(f'  → {pdf_path} ({os.path.getsize(pdf_path)} bytes)')

# Also update the original extracted folder
ios_orig = r"C:/Users/11039/WorkBuddy/国元证券智能门户/_临时/logo_check/元信logo/元信logo/ios"
shutil.copy2(png_path, os.path.join(ios_orig, '登录页logo_93x99.png'))
shutil.copy2(pdf_path, os.path.join(ios_orig, '登录页logo_93x99.pdf'))


# ════════════════════════════════════════════════════
# 4. 重命名 2048x2048 (1).png
# ════════════════════════════════════════════════════

print('\n重命名文件 ...')
old_name = r"C:/Users/11039/WorkBuddy/国元证券智能门户/_临时/logo_check/元信logo/元信logo/2048x2048 (1).png"
new_name = r"C:/Users/11039/WorkBuddy/国元证券智能门户/_临时/logo_check/元信logo/元信logo/only_logo_2048x2048.png"
if os.path.exists(old_name):
    os.rename(old_name, new_name)
    print(f'  → {os.path.basename(old_name)} → {os.path.basename(new_name)}')
else:
    print(f'  ⚠️ 源文件不存在: {old_name}')

print('\n✅ 全部完成！')
print(f'\n输出目录: {OUT_DIR}')
print('  - wework.ico')
print('  - wework_msg_normal.ico')
print('  - ios/登录页logo_93x99.png')
print('  - ios/登录页logo_93x99.pdf')
