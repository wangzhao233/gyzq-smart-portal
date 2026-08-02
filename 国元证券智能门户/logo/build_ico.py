#!/usr/bin/env python3
"""
企业微信本地版 ICO 文件构建器
基于官方 demo 文件逆向分析，精确复刻 BMP/PNG 子图结构。

用法:
  python build_ico.py --src your_logo.png --out output_dir
"""

import struct, io, argparse, os, sys
from pathlib import Path
from PIL import Image

# For Windows GBK terminal, force UTF-8
if sys.platform == 'win32':
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ─── ICO 格式常量 ─────────────────────────────────────

def build_ico_file(entries: list, png_first: bool = False) -> bytes:
    """
    entries: [(w, h, image_data_bytes, is_png, real_bpp), ...]
    排序: 默认 4bit BMP → 8bit → 32bit → PNG (每组大→小)
         png_first=True: PNG → 32bit BMP (大→小)
    """
    bmp_4 = sorted([e for e in entries if not e[3] and e[4] == 4], key=lambda x: (-x[0], -x[1]))
    bmp_8 = sorted([e for e in entries if not e[3] and e[4] == 8], key=lambda x: (-x[0], -x[1]))
    bmp_32 = sorted([e for e in entries if not e[3] and e[4] == 32], key=lambda x: (-x[0], -x[1]))
    pngs = sorted([e for e in entries if e[3]], key=lambda x: (-x[0], -x[1]))
    if png_first:
        ordered = pngs + bmp_32
    else:
        ordered = bmp_4 + bmp_8 + bmp_32 + pngs
    count = len(ordered)

    # 计算偏移量
    header_size = 6 + count * 16
    offsets = []
    cur = header_size
    for w, h, data, *_ in ordered:
        offsets.append(cur)
        cur += len(data)

    # 构建 ICO
    parts = []
    # ICO 文件头
    parts.append(struct.pack('<HHH', 0, 1, count))  # reserved, type=ICO, count

    for i, (w, h, data, is_png, actual_bpp) in enumerate(ordered):
        size = len(data)
        off = offsets[i]
        # ICO 目录项 (16 bytes)
        parts.append(struct.pack('<BBBBHHII',
            w if w < 256 else 0,   # width (0 = 256)
            h if h < 256 else 0,   # height (0 = 256)
            0,                     # color palette count
            0,                     # reserved
            1,                     # color planes
            actual_bpp,            # bits per pixel (real BPP)
            size,                  # image size
            off                    # image offset
        ))

    # 图像数据
    for w, h, data, *_ in ordered:
        parts.append(data)

    return b''.join(parts)


# ─── BMP DIB 构建 (ICO 专用) ──────────────────────────

def build_bmp_dib(img: Image.Image, bpp: int) -> bytes:
    """
    将 PIL Image 转为 ICO 中的 BMP DIB 数据。
    返回完整的 DIB 字节流 (含 XOR + AND 掩码)。
    bpp: 4 | 8 | 32
    """
    w, h = img.size
    if w == 0 or h == 0:
        raise ValueError(f"无效尺寸: {w}x{h}")

    parts = []

    # ── BITMAPINFOHEADER (40 bytes) ──
    # biHeight = 2 * h (ICO 要求 XOR + AND 总高度)
    parts.append(struct.pack('<IiiHHIIiiII',
        40,          # biSize
        w,           # biWidth
        h * 2,       # biHeight (= XOR + AND)
        1,           # biPlanes
        bpp,         # biBitCount
        0,           # biCompression = BI_RGB
        0,           # biSizeImage (可为0)
        0,           # biXPelsPerMeter
        0,           # biYPelsPerMeter
        0,           # biClrUsed
        0            # biClrImportant
    ))

    # ── 调色板 + XOR掩码 ──
    if bpp == 32:
        _build_xor_32bit(parts, img, w, h)
    elif bpp == 8:
        _build_xor_indexed(parts, img, w, h, 256)
    elif bpp == 4:
        _build_xor_indexed(parts, img, w, h, 16)
    else:
        raise ValueError(f"Unsupported bpp: {bpp}")

    # ── AND 掩码 (1位/像素, 4-byte row aligned, 全0=不透明) ──
    and_row_bytes = (w + 7) // 8
    and_row_padded = (and_row_bytes + 3) // 4 * 4
    parts.append(b'\x00' * (and_row_padded * h))

    return b''.join(parts)


def _build_xor_32bit(parts: list, img: Image.Image, w: int, h: int):
    """32位 XOR: BGRA, bottom-up, 4-byte row padded"""
    rgba = img.convert('RGBA')
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b_val, a = rgba.getpixel((x, y))
            row.extend([b_val, g, r, a])
        parts.append(bytes(row))
        # 4-byte row padding is automatic since BGRA = 4 bytes/pixel = always aligned


def _build_xor_indexed(parts: list, img: Image.Image, w: int, h: int, num_colors: int):
    """4-bit 或 8-bit XOR: 索引像素 + 调色板, bottom-up, 4-byte row padded"""
    # 量化 (RGB模式)
    im_p = img.convert('RGB').quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    raw_pal = im_p.getpalette()
    # palette may be shorter than num_colors*3 for images with few colors
    pal_size = min(len(raw_pal), num_colors * 3)
    palette = raw_pal[:pal_size]
    if len(palette) < num_colors * 3:
        palette = palette + [0] * (num_colors * 3 - len(palette))

    # 调色表: 每色 BGRA (4 bytes)
    for i in range(num_colors):
        r, g, b_val = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
        parts.append(struct.pack('BBBB', b_val, g, r, 0))

    if num_colors == 256:
        # 8-bit: 1 byte/pixel
        for y in range(h - 1, -1, -1):
            row = bytearray()
            for x in range(w):
                row.append(im_p.getpixel((x, y)))
            parts.append(bytes(row))
            # 4-byte row padding
            pad = (4 - w % 4) % 4
            if pad:
                parts.append(b'\x00' * pad)
    else:
        # 4-bit: 2 pixels/byte, high nibble first (left pixel)
        for y in range(h - 1, -1, -1):
            row = bytearray()
            for x in range(0, w, 2):
                left = im_p.getpixel((x, y))
                right = im_p.getpixel((x + 1, y)) if x + 1 < w else 0
                row.append((left << 4) | right)
            parts.append(bytes(row))
            # 4-byte row padding
            row_bytes = (w + 1) // 2
            pad = (4 - row_bytes % 4) % 4
            if pad:
                parts.append(b'\x00' * pad)


# ─── PNG 编码 ─────────────────────────────────────────

def encode_png(img: Image.Image, size: int) -> bytes:
    im = img.resize((size, size), Image.LANCZOS).convert('RGBA')
    buf = io.BytesIO()
    im.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


# ─── 托盘图标辅助 ─────────────────────────────────────

def to_tray_icon(img: Image.Image, size: int) -> Image.Image:
    """托盘图标: 白底不透明"""
    im = img.resize((size, size), Image.LANCZOS).convert('RGBA')
    bg = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    bg.paste(im, (0, 0), im)
    return bg


# ─── 主流程 ───────────────────────────────────────────

def generate_icos(src_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Image.open(str(src_path)).convert('RGBA')
    print(f"Source: {src.size[0]}x{src.size[1]}")

    # ═══ wework.ico ═══
    # 按物料清单: 6 BMP (128/64/48/40/32/16) + 3 PNG (256/512/1024)
    # ICO目录项宽度高度字段只有1字节(0=256), 512/1024用实际PNG分辨率承载
    print("\n[1/2] Building wework.ico ...")
    entries = []

    # PNG entries: 实际尺寸 256, 512, 1024; 目录项标记为 0(256)
    png_configs = [(256, 256), (0, 512), (0, 1024)]  # (dir_entry, actual)
    for dir_val, actual in png_configs:
        data = encode_png(src, actual)
        entries.append((dir_val, dir_val, data, True, 32))
        label = f'{actual}x{actual}' if dir_val == 0 else f'{dir_val}x{dir_val}'
        print(f"  PNG 实际{actual}x{actual} 目录项{dir_val}x{dir_val}  {len(data):,}B")

    # BMP entries (all 32-bit)
    for s in [128, 64, 48, 40, 32, 16]:
        im = src.resize((s, s), Image.LANCZOS).convert('RGBA')
        data = build_bmp_dib(im, 32)
        entries.append((s, s, data, False, 32))
        print(f"  BMP {s}x{s} 32bit  {len(data):,}B")

    wework_path = out_dir / 'wework.ico'
    wework_path.write_bytes(build_ico_file(entries, png_first=True))
    print(f"  Done: wework.ico ({wework_path.stat().st_size:,}B)")

    # ═══ wework_msg_normal.ico ═══
    # 官方demo结构: 4-bit(2) + 8-bit(3) + 32-bit(7) = 12 BMP
    print("\n[2/2] Building wework_msg_normal.ico ...")
    entries = []

    # 4-bit: 32, 16
    for s in [32, 16]:
        im = to_tray_icon(src, s)
        data = build_bmp_dib(im, 4)
        entries.append((s, s, data, False, 4))
        print(f"  BMP {s}x{s} 4bit  {len(data):,}B")

    # 8-bit: 48, 32, 16
    for s in [48, 32, 16]:
        im = to_tray_icon(src, s)
        data = build_bmp_dib(im, 8)
        entries.append((s, s, data, False, 8))
        print(f"  BMP {s}x{s} 8bit  {len(data):,}B")

    # 32-bit: 64, 48, 40, 32, 24, 20, 16
    for s in [64, 48, 40, 32, 24, 20, 16]:
        im = to_tray_icon(src, s)
        data = build_bmp_dib(im, 32)
        entries.append((s, s, data, False, 32))
        print(f"  BMP {s}x{s} 32bit  {len(data):,}B")

    msg_path = out_dir / 'wework_msg_normal.ico'
    msg_path.write_bytes(build_ico_file(entries))
    print(f"  Done: wework_msg_normal.ico ({msg_path.stat().st_size:,}B)")

    # ── 校验 ──
    print("\n" + "=" * 50)
    print("Verification:")
    verify_ico(wework_path, expected_total=9)
    verify_ico(msg_path, expected_total=12)

    # 与官方demo对比
    print("\n" + "=" * 50)
    print("Comparison with official demo:")
    compare_with_demo(wework_path, 'wework.ico')
    compare_with_demo(msg_path, 'wework_msg_normal.ico')


def verify_ico(path: Path, expected_total: int):
    data = path.read_bytes()
    magic = struct.unpack_from('<HHH', data, 0)
    if magic != (0, 1, expected_total):
        print(f"  WARN: {path.name} header={magic} expected=(0,1,{expected_total})")
        return

    print(f"  OK: {path.name}  {expected_total} images  {len(data):,}B")

    bmp_count = png_count = 0
    for i in range(expected_total):
        off = 6 + i * 16
        entry = data[off:off+16]
        w = entry[0] if entry[0] != 0 else 256
        h = entry[1] if entry[1] != 0 else 256
        bpp = int.from_bytes(entry[6:8], 'little')
        size = int.from_bytes(entry[8:12], 'little')
        img_off = int.from_bytes(entry[12:16], 'little')
        if img_off + 4 > len(data):
            print(f"    [{i}] OFFSET ERROR: img_off={img_off} > file_size={len(data)}")
            continue
        img_head = data[img_off:img_off+4]
        if img_head == b'\x89PNG':
            fmt = 'PNG'
            png_count += 1
        elif img_head == struct.pack('<I', 40):
            fmt = 'BMP'
            bmp_count += 1
        else:
            fmt = f'??? ({img_head.hex()})'
        print(f"    [{i}] {w}x{h} {bpp}bit {size:,}B {fmt}")
    print(f"  Summary: {bmp_count} BMP + {png_count} PNG")


def compare_with_demo(our_path: Path, fname: str):
    """与官方demo对比"""
    import zipfile
    demo_zip = Path(__file__).resolve().parent.parent / '附件8_客户端和管理后台logo_demo.zip'
    if not demo_zip.exists():
        print(f"  (demo zip not found, skipping comparison)")
        return

    zf = zipfile.ZipFile(str(demo_zip))
    demo_data = None
    for name in zf.namelist():
        if name.endswith(fname) and not '__MACOSX' in name:
            demo_data = zf.read(name)
            break

    if not demo_data:
        print(f"  ({fname} not found in demo)")
        return

    our_data = our_path.read_bytes()
    print(f"  Demo: {len(demo_data):,}B  |  Ours: {len(our_data):,}B")

    # 对比子图数量
    demo_count = int.from_bytes(demo_data[4:6], 'little')
    our_count = int.from_bytes(our_data[4:6], 'little')
    print(f"  Images: Demo={demo_count}  Ours={our_count}")

    # 对比各尺寸格式
    demo_info = _scan_ico(demo_data, demo_count)
    our_info = _scan_ico(our_data, our_count)
    print(f"  Demo sizes: {demo_info}")
    print(f"  Ours sizes: {our_info}")


def _scan_ico(data: bytes, count: int) -> list:
    result = []
    for i in range(count):
        off = 6 + i * 16
        entry = data[off:off+16]
        w = entry[0] if entry[0] != 0 else 256
        h = entry[1] if entry[1] != 0 else 256
        bpp = int.from_bytes(entry[6:8], 'little')
        img_off = int.from_bytes(entry[12:16], 'little')
        fmt = 'PNG' if data[img_off:img_off+4] == b'\x89PNG' else 'BMP'
        result.append(f"{w}x{h}/{bpp}b/{fmt}")
    return result


def main():
    p = argparse.ArgumentParser(description='WeCom Local ICO Builder')
    p.add_argument('--src', type=Path, required=True, help='Source logo PNG')
    p.add_argument('--out', type=Path, default=Path(__file__).parent / 'output' / 'pc',
                   help='Output directory')
    # 也支持通过环境变量或默认覆盖
    args = p.parse_args()

    if not args.src.exists():
        print(f"ERROR: Source file not found: {args.src}")
        sys.exit(1)

    generate_icos(args.src, args.out)


if __name__ == '__main__':
    main()
