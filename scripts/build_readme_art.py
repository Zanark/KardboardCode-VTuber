"""Build GitHub-safe README banners from the supplied logo and licensed local fonts."""

from __future__ import annotations

import argparse
import random
import tomllib
from pathlib import Path

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


def section(number: str, title: str, subtitle: str, filename: str) -> None:
    image = paper(196)
    draw = ImageDraw.Draw(image)
    draw.rectangle((42, 43, 149, 151), fill=INK)
    text(image, (58, 76), number, 43, fill=MINT, pixel=True, bold=True)
    text(image, (190, 44), title, 65, bold=True)
    text(image, (193, 124), subtitle, 23, pixel=True)
    save(image, filename)


def features() -> None:
    image = paper(338)
    draw = ImageDraw.Draw(image)
    cards = (
        ("3D", "A REAL LITTLE BOX", "Textured geometry + spring flaps"),
        ("K C", "EYES WITH PERSONALITY", "Independent blink + wink controls"),
        ("OUT", "CAMERA-READY OUTPUT", "Clean video via OBS Virtual Camera"),
    )
    for index, (mark, title, caption) in enumerate(cards):
        left = 38 + index * 514
        draw.rectangle((left, 38, left + 496, 299), fill=CREAM, outline=INK, width=2)
        draw.rectangle((left + 22, 59, left + 146, 128), fill=INK)
        text(image, (left + 37, 77), mark, 33, fill=MINT, pixel=True, bold=True)
        text(image, (left + 22, 160), title, 37, bold=True)
        text(image, (left + 22, 220), caption, 29)
    save(image, "feature-cards.png")


def footer() -> None:
    image = paper(292, dark=True)
    logo(image, (50, 37, 278, 256))
    text(image, (330, 65), "HANDLE WITH CHARACTER.", 59, fill=CREAM, pixel=True, bold=True)
    text(image, (335, 164), "Built in Python. Wrapped in cardboard.", 45, fill=MINT)
    save(image, "footer.png")


def build() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    hero(version)
    features()
    sections = (
        ("01", "THE CONTROL ROOM", "REAL WIDGETS / LIVE SLIDERS / YOUR SETUP", "studio.png"),
        ("02", "BUILT TO MOVE", "REAL 3D / LITTLE PIXELS / BIG EXPRESSIONS", "motion.png"),
        (
            "03", "EVERY SIDE HAS A STORY",
            "CORRUGATION / SHIPPING LABELS / HEADPHONES", "details.png",
        ),
        ("04", "UNDER THE CARDBOARD", "SYNTHETIC DEBUG VIEWS / REAL GEOMETRY", "debug.png"),
        (
            "05", "UNBOX YOUR SETUP",
            "QUICK START / CAMERA OUTPUT / THE ENGINEERING BOOK", "start.png",
        ),
    )
    for number, title, subtitle, filename in sections:
        section(number, title, subtitle, filename)
    footer()


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        build()
    except (OSError, ValueError) as error:
        raise SystemExit(f"README artwork build failed: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
