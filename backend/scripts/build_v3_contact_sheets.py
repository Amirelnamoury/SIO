"""Crop mobile audit screenshots and build visual-review contact sheets."""

from __future__ import annotations

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def contact_sheet(files: list[Path], output: Path, *, tile: tuple[int, int], columns: int, transform=None) -> None:
    label_height = 28
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new("RGB", (tile[0] * columns, (tile[1] + label_height) * rows), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, path in enumerate(files):
        source = Image.open(path).convert("RGB")
        if transform:
            source = transform(source)
        preview = ImageOps.fit(source, tile, method=Image.Resampling.LANCZOS, centering=(0.5, 0.0))
        x = (index % columns) * tile[0]
        y = (index // columns) * (tile[1] + label_height)
        sheet.paste(preview, (x, y))
        draw.text((x + 7, y + tile[1] + 7), path.stem, fill="#171717", font=font)
    sheet.save(output, quality=92)


def silhouette(image: Image.Image) -> Image.Image:
    grey = ImageOps.grayscale(image).filter(ImageFilter.GaussianBlur(radius=10))
    return ImageOps.posterize(grey, 2).convert("RGB")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Audit directory required")
    root = Path(sys.argv[1]).resolve()
    mobile = root / "mobile"
    mobile.mkdir(exist_ok=True)
    for source in sorted((root / "mobile-raw").glob("*.png")):
        image = Image.open(source).convert("RGB")
        image.crop((0, 0, min(390, image.width), image.height)).save(mobile / source.name)
    desktop_files = sorted((root / "desktop").glob("*.png"))
    mobile_files = sorted(mobile.glob("*.png"))
    contact_sheet(desktop_files, root / "contact-sheet-desktop.jpg", tile=(360, 203), columns=3)
    contact_sheet(mobile_files, root / "contact-sheet-mobile.jpg", tile=(195, 360), columns=6)
    contact_sheet(desktop_files, root / "contact-sheet-grayscale-desktop.jpg", tile=(360, 203), columns=3, transform=lambda image: ImageOps.grayscale(image).convert("RGB"))
    contact_sheet(desktop_files, root / "contact-sheet-silhouette.jpg", tile=(360, 203), columns=3, transform=silhouette)
    print(f"Built 18 desktop and {len(mobile_files)} mobile audit tiles")


if __name__ == "__main__":
    main()
