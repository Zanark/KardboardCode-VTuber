"""Build GitHub-safe README banners from the supplied logo and licensed local fonts."""

from __future__ import annotations

import argparse
import random
import tomllib
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "docs" / "branding" / "fonts"
OUTPUT = ROOT / "docs" / "images" / "readme"
INK = "#19332b"
PAPER = "#f3e7cc"
KRAFT = "#d5a568"
MINT = "#9ce3bc"
CREAM = "#fff4db"
WIDTH = 1600


def font(size: int, *, pixel: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = (
        f"Silkscreen-{'Bold' if bold else 'Regular'}.ttf"
        if pixel else f"BarlowCondensed-{'SemiBold' if bold else 'Regular'}.ttf"
    )
    return ImageFont.truetype(str(FONTS / name), size)


def text(
    image: Image.Image, position: tuple[int, int], value: str, size: int,
    *, fill: str = INK, pixel: bool = False, bold: bool = False,
) -> None:
    face = font(size, pixel=pixel, bold=bold)
    if position[0] + face.getlength(value) > image.width - 35:
        raise ValueError(f"Banner text would overflow: {value}")
    ImageDraw.Draw(image).text(position, value, font=face, fill=fill, anchor="lt")


def paper(height: int, *, dark: bool = False) -> Image.Image:
    image = Image.new("RGB", (WIDTH, height), INK if dark else PAPER)
    draw = ImageDraw.Draw(image)
    rng = random.Random(7381 + height)
    colors = ("#1d382e", "#203c32") if dark else ("#e9dcbf", "#ecdfc3")
    for _ in range(height * 4):
        x, y = rng.randrange(WIDTH), rng.randrange(height)
        draw.line((x, y, x + rng.randrange(1, 5), y), fill=rng.choice(colors))
    for x in range(24, WIDTH, 48):
        draw.line((x, 0, x, height), fill="#244135" if dark else "#ebddbe")
    draw.rectangle((16, 16, WIDTH - 17, height - 17), outline=MINT if dark else INK, width=2)
    return image


def barcode(draw: ImageDraw.ImageDraw, x: int, y: int, *, fill: str = INK) -> None:
    rng = random.Random(42)
    for _ in range(40):
        width = rng.choice((2, 3, 5))
        draw.rectangle((x, y, x + width, y + 42), fill=fill)
        x += width + rng.choice((3, 5))


def logo(image: Image.Image, box: tuple[int, int, int, int]) -> None:
    source = ROOT / "src" / "kardboard_vtuber" / "gui" / "assets" / "kardboardcode-logo.png"
    with Image.open(source) as master:
        artwork = master.convert("RGBA")
    bounds = artwork.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("The supplied logo is fully transparent")
    artwork = artwork.crop(bounds)
    artwork.thumbnail((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
    left = box[0] + (box[2] - box[0] - artwork.width) // 2
    top = box[1] + (box[3] - box[1] - artwork.height) // 2
    image.paste(artwork, (left, top), artwork)


def save(image: Image.Image, name: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    image.save(path, optimize=True)
    print(f"{path.name}: {image.width}x{image.height} / {path.stat().st_size:,} bytes")


def hero(version: str) -> None:
    image = paper(740, dark=True)
    draw = ImageDraw.Draw(image)
    draw.polygon(((1000, 17), (1582, 17), (1582, 722), (850, 722)), fill=KRAFT)
    for x in range(1000, 1580, 28):
        draw.line((x, 18, x, 721), fill="#cca069")
    draw.polygon(((1000, 17), (1058, 17), (906, 722), (850, 722)), fill="#b68e59")
    draw.rectangle((69, 64, 594, 106), fill=MINT)
    text(image, (88, 75), "NATIVE PYTHON / VTUBER", 24, pixel=True)
    text(image, (70, 160), "KARDBOARD", 86, fill=CREAM, pixel=True, bold=True)
    text(image, (73, 270), "CODE / STUDIO", 106, fill=MINT, bold=True)
    text(image, (76, 424), "Your camera. Your cardboard.", 51, fill=CREAM)
    text(image, (77, 493), "Real 3D. Live eyes. Zero browser tabs.", 32, fill="#cfdbc6")
    draw.rectangle((76, 590, 685, 662), outline="#6c8c75", width=2)
    text(image, (96, 614), f"v{version} / SOURCE EDITION", 25, fill=CREAM, pixel=True)
    logo(image, (952, 120, 1545, 632))
    barcode(draw, 1128, 665)
    text(image, (1194, 69), "HANDLE WITH", 25, pixel=True)
    text(image, (1194, 105), "CHARACTER.", 25, pixel=True)
    save(image, "hero.png")


def svg_text(
    value: str, x: int, y: int, size: int, *, pixel: bool = False,
    fill: str = KRAFT,
) -> str:
    filename = "Silkscreen-Bold.ttf" if pixel else "BarlowCondensed-SemiBold.ttf"
    parts = []
    with TTFont(FONTS / filename) as face:
        glyphs = face.getGlyphSet()
        cmap = face.getBestCmap()
        scale = size / face["head"].unitsPerEm
        baseline = y + face["hhea"].ascent * scale
        cursor = float(x)
        for character in value:
            name = cmap.get(ord(character))
            if name is None:
                raise ValueError(f"Font has no SVG glyph for {character!r}")
            glyph = glyphs[name]
            pen = SVGPathPen(glyphs)
            glyph.draw(pen)
            data = pen.getCommands()
            if data:
                parts.append(
                    f'<path d="{data}" fill="{fill}" stroke="{INK}" stroke-width="1" '
                    'paint-order="stroke" vector-effect="non-scaling-stroke" '
                    f'transform="translate({cursor:.3f} {baseline:.3f}) '
                    f'scale({scale:.6f} {-scale:.6f})"/>',
                )
            cursor += glyph.width * scale
        if cursor > WIDTH - 24:
            raise ValueError(f"SVG lettering would overflow: {value}")
    return "".join(parts)


def save_svg(filename: str, body: str, title: str, *, height: int = 170) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img"><title>{escape(title)}</title>'
        f"{body}</svg>\n"
    )
    (OUTPUT / filename).write_text(data, encoding="utf-8", newline="\n")
    print(f"{filename}: transparent vector lettering")


def section(number: str, title: str, subtitle: str, filename: str) -> None:
    body = (
        f'<rect x="22" y="26" width="104" height="104" rx="8" fill="{INK}"/>'
        + svg_text(number, 36, 44, 44, pixel=True, fill=MINT)
        + svg_text(title, 160, 12, 63)
        + svg_text(subtitle, 163, 96, 22, pixel=True, fill=MINT)
    )
    save_svg(filename, body, title)


def footer() -> None:
    save_svg(
        "footer.svg",
        svg_text("HANDLE WITH CHARACTER.", 80, 16, 64, pixel=True)
        + svg_text("Built in Python. Wrapped in cardboard.", 84, 108, 40, fill=MINT),
        "Handle with character",
    )


def avatar_hero() -> None:
    import cv2
    import numpy as np

    from kardboard_vtuber.renderer import Textured3DCardboardRenderer
    from kardboard_vtuber.tracking.models import FaceTrackingState, HeadPose

    image = paper(760, dark=True)
    draw = ImageDraw.Draw(image)
    draw.rectangle((880, 76, 1532, 674), fill=KRAFT)
    draw.rectangle((904, 100, 1508, 650), outline=INK, width=2)
    text(image, (940, 135), "THE ACTUAL", 28, pixel=True)
    text(image, (934, 211), "3D AVATAR", 98, bold=True)
    text(image, (940, 355), "Small box.", 70, bold=True)
    text(image, (940, 440), "Big character.", 70, bold=True)
    text(image, (943, 572), "ModernGL / MediaPipe / OpenCV", 31)
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    renderer = Textured3DCardboardRenderer()
    try:
        renderer.render(frame, FaceTrackingState(
            timestamp_ms=1, detected=True, landmarks=(), center_x=.27, center_y=.61,
            face_width=.095, face_height=.105, left_eye_open=1, right_eye_open=1,
            mouth_open=0, head_pose=HeadPose(0, 0, 0, -18, 30, -2),
        ))
    finally:
        renderer.close()
    path = ROOT / "docs" / "images" / "kardboardcode-hero.png"
    Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(path, optimize=True)
    print(f"{path.name}: runtime avatar / matching forest and kraft palette")


def build() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    hero(version)
    sections = (
        ("01", "THE CONTROL ROOM", "REAL WIDGETS / LIVE SLIDERS / YOUR SETUP", "studio.svg"),
        ("02", "BUILT TO MOVE", "REAL 3D / LITTLE PIXELS / BIG EXPRESSIONS", "motion.svg"),
        (
            "03", "EVERY SIDE HAS A STORY",
            "CORRUGATION / SHIPPING LABELS / HEADPHONES", "details.svg",
        ),
        ("04", "UNDER THE CARDBOARD", "SYNTHETIC DEBUG VIEWS / REAL GEOMETRY", "debug.svg"),
        (
            "05", "UNBOX YOUR SETUP",
            "QUICK START / CAMERA OUTPUT / THE ENGINEERING BOOK", "start.svg",
        ),
    )
    for number, title, subtitle, filename in sections:
        section(number, title, subtitle, filename)
    footer()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--avatar-hero", action="store_true", help="Also rebuild the GPU avatar hero.",
    )
    args = parser.parse_args()
    try:
        build()
        if args.avatar_hero:
            avatar_hero()
    except (OSError, ValueError) as error:
        raise SystemExit(f"README artwork build failed: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
