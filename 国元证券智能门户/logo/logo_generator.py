#!/usr/bin/env python3
"""
国元证券企业微信本地版 - Logo物料批量生成脚本
基于「附件4_简化版-logo物料清单.xlsx」自动生成各平台所需logo

用法：
  python logo_generator.py                    # 默认源: iOS.png (1024×1024)
  python logo_generator.py --src 你的logo.png # 指定源图
  python logo_generator.py --check-only       # 仅验证已生成文件

生成清单 (8项自动 + 5项需设计师)：
  ✅ Android:    ic_launcher2x(96×96) / ic_launcher3x(144×144)
  ✅ iOS:        logo_1024.png / logo_login.pdf
  ✅ PC:         appicon@2x.png / wework.ico(7合1) / wework_msg_normal.ico(12合1)
  ✅ Web:        favicon.ico
  ⚠️ 设计师:    公用素材3项(2048×2048含文字) + Web端2项(含文字)
"""

import os, sys, argparse
from pathlib import Path
from PIL import Image

# ─── 配置 ────────────────────────────────────────────
SELF_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SELF_DIR / "output"
DEFAULT_SRC = SELF_DIR / "iOS.png"
LOGIN_LOGO_SRC = SELF_DIR / "元信LOGO@1x.png"


def ensure_dir(p: Path) -> Path:
    os.makedirs(str(p), exist_ok=True)
    return p


def resize(src: Image.Image, size: tuple, out: Path) -> Path:
    img = src.resize(size, Image.LANCZOS)
    img.save(str(out), format="PNG", optimize=True)
    return out


def create_ico(src: Image.Image, sizes: list, out: Path) -> Path:
    """多尺寸ICO，使用PNG子图（Vista+兼容，含透明通道）"""
    src.save(str(out), format="ICO", sizes=sizes)
    return out


def create_tray_ico(src: Image.Image, sizes: list, out: Path) -> Path:
    """
    托盘图标ICO：白底合成（托盘区无透明背景），多尺寸。
    ICO标准最大256×256，所有≤256尺寸统一打包。
    """
    bg = Image.new("RGB", src.size, (255, 255, 255))
    bg.paste(src, mask=src.split()[3] if src.mode == "RGBA" else None)
    bg.save(str(out), format="ICO", sizes=sizes)
    return out


def create_pdf(src: Image.Image, size: tuple, out: Path) -> Path:
    src.resize(size, Image.LANCZOS).save(str(out), format="PDF", resolution=72)
    return out


def verify(filepath: Path, expected_size: tuple = None) -> tuple:
    if not filepath.exists():
        return False, "文件不存在"
    fsize = filepath.stat().st_size
    if fsize == 0:
        return False, "文件为空"
    suf = filepath.suffix.lower()
    if suf == '.png':
        im = Image.open(filepath)
        if expected_size and im.size != expected_size:
            return False, f"尺寸不匹配 期望{expected_size} 实际{im.size}"
        return True, f"{im.size[0]}×{im.size[1]}  {fsize:,}B"
    elif suf == '.ico':
        im = Image.open(filepath)
        sz_info = im.info.get('sizes', set())
        return True, f"{len(sz_info)}个尺寸  {fsize:,}B  {sorted(sz_info)}"
    elif suf == '.pdf':
        return True, f"{fsize:,}B"
    return True, f"{fsize:,}B"


# ─── 主流程 ────────────────────────────────────────────

def generate_all(src_path: Path):
    print("=" * 60)
    print("  国元证券 · 企微本地版 Logo 批量生成")
    print("=" * 60)

    if not src_path.exists():
        print(f"\n❌ 源文件不存在: {src_path}")
        sys.exit(1)

    src = Image.open(src_path)
    if src.mode != "RGBA":
        src = src.convert("RGBA")
    print(f"\n📥 源图: {src_path.name}  {src.size[0]}×{src.size[1]}  {src.mode}")
    print(f"📁 输出: {OUTPUT_DIR}\n")

    results = []
    errors = []

    def do(name, fn):
        try:
            path = fn()
            ok, msg = verify(path)
            results.append((name, str(path.relative_to(SELF_DIR)), ok, msg))
            status = "✅" if ok else "❌"
            print(f"  {status} {name:<40s} {msg}")
        except Exception as e:
            errors.append((name, str(e)))
            print(f"  ❌ {name:<40s} {e}")

    # ═══════ Android ═══════
    ad = ensure_dir(OUTPUT_DIR / "android")
    do("Android 桌面图标 96×96",  lambda: resize(src, (96, 96), ad / "ic_launcher2x.png"))
    do("Android 桌面图标 144×144", lambda: resize(src, (144, 144), ad / "ic_launcher3x.png"))

    # ═══════ iOS ═══════
    ios_d = ensure_dir(OUTPUT_DIR / "ios")
    do("iOS AppIcon 1024×1024", lambda: (
        src.save(str(ios_d / "logo_1024.png"), format="PNG", optimize=True),
        ios_d / "logo_1024.png")[1])

    login_src = Image.open(LOGIN_LOGO_SRC) if LOGIN_LOGO_SRC.exists() else src
    if LOGIN_LOGO_SRC.exists():
        print(f"     ℹ️  登录页logo源: {LOGIN_LOGO_SRC.name}")
    do("iOS 登录页logo PDF 144×144", lambda: create_pdf(login_src, (144, 144), ios_d / "logo_login.pdf"))

    # ═══════ PC端 ═══════
    pc = ensure_dir(OUTPUT_DIR / "pc")
    do("PC 桌面logo 1024×1024", lambda: resize(src, (1024, 1024), pc / "appicon_512x512@2x.png"))

    # wework.ico: ≤256尺寸入ICO, 512/1024单独PNG (ICO标准最大256)
    wework_ico_sizes = [(16, 16), (32, 32), (40, 40), (48, 48),
                         (64, 64), (128, 128), (256, 256)]
    do("PC wework.ico (7合1)", lambda: create_ico(src, wework_ico_sizes, pc / "wework.ico"))
    do("PC wework内嵌 512×512", lambda: resize(src, (512, 512), pc / "wework_512.png"))
    do("PC wework内嵌 1024×1024", lambda: resize(src, (1024, 1024), pc / "wework_1024.png"))

    # wework_msg_normal.ico: 托盘图标（白底多尺寸）
    msg_sizes = [
        (16, 16), (32, 32), (16, 16), (32, 32), (48, 48),
        (16, 16), (20, 20), (24, 24), (32, 32), (40, 40),
        (48, 48), (64, 64),
    ]
    do("PC 托盘图标 (12合1)", lambda: create_tray_ico(src, msg_sizes, pc / "wework_msg_normal.ico"))

    # ═══════ Web端 ═══════
    web = ensure_dir(OUTPUT_DIR / "web")
    do("Web favicon.ico 48×48", lambda: create_ico(src, [(48, 48)], web / "favicon.ico"))

    # ── 终报 ──────────────────────────────────────────
    ok_count = sum(1 for _, _, ok, _ in results if ok)
    fail_count = len(results) - ok_count + len(errors)

    print(f"\n{'─' * 60}")
    print(f"  ⚠️  需要设计师提供 ({5}项)")
    print(f"{'─' * 60}")
    designer = [
        ("公用素材", "logo_vertical_text.png", "2048×2048", "竖排文字logo排版"),
        ("公用素材", "logo_and_horizontal_text.png", "2048×468", "横排文字logo排版"),
        ("公用素材", "only_logo.png", "2048×2048", "纯logo矢量版(1024→2048会模糊)"),
        ("Web端", "LoginLogo_3x.png", "780×90", "登录页含「政务微信」文字"),
        ("Web端", "apiLogo_3x.png", "498×78", "API logo含文字"),
    ]
    for plat, fn, sz, note in designer:
        print(f"  📐 [{plat}] {fn} ({sz}) — {note}")

    print(f"\n{'═' * 60}")
    print(f"  自动生成: {ok_count}/{len(results)} 成功"
          + (f"  ⚠️ {fail_count} 失败" if fail_count else ""))
    print(f"  设计师待处理: 5项")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"{'═' * 60}")


def main():
    p = argparse.ArgumentParser(description="企微本地版 Logo批量生成")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC, help="源图路径")
    p.add_argument("--check-only", action="store_true", help="仅验证")
    args = p.parse_args()

    if args.check_only:
        print("🔍 验证模式\n")
        all_ok = True
        for root, _, files in os.walk(OUTPUT_DIR):
            for f in files:
                fp = Path(root) / f
                ok, msg = verify(fp)
                print(f"  {'✅' if ok else '❌'} {fp.relative_to(SELF_DIR)} — {msg}")
                if not ok:
                    all_ok = False
        print(f"\n{'✅ 全部通过' if all_ok else '❌ 有问题，请重新生成'}")
        sys.exit(0 if all_ok else 1)

    generate_all(args.src)


if __name__ == "__main__":
    main()
