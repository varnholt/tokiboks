#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


CARD_RATIO = 54 / 85.6  # portrait credit card width / height
CARD_WIDTH_MM = 54
CARD_HEIGHT_MM = 85.6
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
DPI_300 = 300
MM_PER_INCH = 25.4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create portrait credit-card artwork images from album front/back covers, "
            "leaving a white bottom area for later overlay."
        )
    )

    parser.add_argument(
        "--front",
        type=Path,
        required=True,
        help="front cover image",
    )
    parser.add_argument(
        "--back",
        type=Path,
        default=None,
        help="optional back cover image",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="output directory (default: current directory)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1080,
        help="output width in pixels (default: 1080)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1712,
        help="output height in pixels (default: 1712, matches portrait credit-card ratio)",
    )
    parser.add_argument(
        "--bottom-fraction",
        type=float,
        default=0.22,
        help="fraction of total height reserved as white bottom area (default: 0.22)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="scale factor for the artwork (default: 1.0, use >1.0 to cover more of the bottom area)",
    )
    parser.add_argument(
        "--cutting-guide",
        action="store_true",
        help="draw rounded corner cutting guide lines",
    )
    parser.add_argument(
        "--corner-radius",
        type=int,
        default=80,
        help="corner radius in pixels for cutting guide (default: 80)",
    )
    parser.add_argument(
        "--color-bottom",
        action="store_true",
        help="fill bottom area with 5 dominant colors from the image instead of white",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="resize longer side to this many pixels before color analysis (default: 300)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="also create an A4 portrait PDF at 300 DPI with front and back images",
    )
    parser.add_argument(
        "--rfid",
        type=str,
        choices=["white", "black"],
        default=None,
        help="add RFID icon (white or black) on the bottom area",
    )
    parser.add_argument(
        "--bleed",
        type=float,
        default=0.0,
        help="bleed margin in mm to add around the card (default: 0.0)",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.front.is_file():
        raise FileNotFoundError(f"front image not found: {args.front}")

    if args.back is not None and not args.back.is_file():
        raise FileNotFoundError(f"back image not found: {args.back}")

    if args.width <= 0 or args.height <= 0:
        raise ValueError("width and height must be positive")

    if not (0.0 < args.bottom_fraction < 1.0):
        raise ValueError("bottom-fraction must be between 0 and 1")

    actual_ratio = args.width / args.height
    expected_ratio = CARD_RATIO

    if abs(actual_ratio - expected_ratio) > 0.02:
        raise ValueError(
            f"output size must match portrait credit-card ratio approximately "
            f"({expected_ratio:.4f}), got {actual_ratio:.4f}"
        )


def fit_image_to_area(
    image: Image.Image, target_width: int, target_height: int, scale: float = 1.0
) -> tuple[Image.Image, int, int]:
    """
    Scale image to fit within the target area (letterbox/pillarbox if needed).
    Returns the resized image and the offset (x, y) to center it.
    
    If scale > 1.0, the image is scaled up to cover more area (may crop edges).
    """
    source_width, source_height = image.size
    source_ratio = source_width / source_height
    target_ratio = target_width / target_height

    if source_ratio > target_ratio:
        scaled_width = target_width
        scaled_height = round(target_width / source_ratio)
    else:
        scaled_height = target_height
        scaled_width = round(target_height / source_ratio)

    # Apply additional scale factor
    scaled_width = round(scaled_width * scale)
    scaled_height = round(scaled_height * scale)

    resized = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    offset_x = (target_width - scaled_width) // 2
    offset_y = (target_height - scaled_height) // 2

    return resized, offset_x, offset_y


def extract_top_five_colors(image: Image.Image) -> list[tuple[int, int, int]]:
    """
    Extract 5 representative colors using Pillow's adaptive palette quantization.
    Returns colors sorted by frequency, most common first.
    """
    quantized = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=5)
    palette = quantized.getpalette()
    color_counts = quantized.getcolors()

    if color_counts is None:
        raise RuntimeError("failed to extract color counts from quantized image")

    sorted_counts = sorted(color_counts, reverse=True)

    colors: list[tuple[int, int, int]] = []
    for _count, palette_index in sorted_counts[:5]:
        red = palette[palette_index * 3]
        green = palette[palette_index * 3 + 1]
        blue = palette[palette_index * 3 + 2]
        colors.append((red, green, blue))

    if len(colors) < 5:
        last_color = colors[-1] if len(colors) > 0 else (0, 0, 0)
        while len(colors) < 5:
            colors.append(last_color)

    return colors


def create_palette_strip(
    colors: list[tuple[int, int, int]],
    width: int,
    height: int,
) -> Image.Image:
    """Create a horizontal color palette strip with 5 colors."""
    palette_image = Image.new("RGB", (width, height), (255, 255, 255))
    box_width = width // 5

    for index, color in enumerate(colors):
        left = index * box_width
        right = (index + 1) * box_width if index < 4 else width
        box = Image.new("RGB", (right - left, height), color)
        palette_image.paste(box, (left, 0))

    return palette_image


def resize_for_analysis(image: Image.Image, sample_size: int) -> Image.Image:
    """Resize image for color analysis."""
    width, height = image.size

    if width >= height:
        new_width = sample_size
        new_height = max(1, int(height * sample_size / width))
    else:
        new_height = sample_size
        new_width = max(1, int(width * sample_size / height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def draw_cutting_guide(
    card: Image.Image,
    radius: int,
    color: tuple[int, int, int] = (255, 0, 0),
    bleed: float = 0.0,
) -> None:
    """Draw rounded corner cutting guide lines on the card.

    Args:
        card: The card image (may include bleed area).
        radius: Corner radius in pixels.
        color: Line color as RGB tuple.
        bleed: Bleed margin in mm. The guide is drawn at the cut line (card size minus bleed).
    """
    draw = ImageDraw.Draw(card)
    width, height = card.size

    # Convert bleed from mm to pixels and calculate the cut line
    bleed_px = round(bleed / MM_PER_INCH * DPI_300) if bleed > 0 else 0
    margin = 5 + bleed_px  # small margin from cut line, plus any bleed offset

    left = margin
    top = margin
    right = width - margin
    bottom = height - margin

    draw.rounded_rectangle(
        [(left, top), (right, bottom)],
        radius=radius,
        outline=color,
        width=3,
    )


def create_card_image(
    input_path: Path,
    output_path: Path,
    card_width: int,
    card_height: int,
    bottom_fraction: float,
    scale: float = 1.0,
    cutting_guide: bool = False,
    corner_radius: int = 80,
    color_bottom: bool = False,
    sample_size: int = 300,
    rfid: str | None = None,
    bleed: float = 0.0,
) -> None:
    image = Image.open(input_path).convert("RGB")

    bottom_height = round(card_height * bottom_fraction)
    art_height = card_height - bottom_height

    artwork, offset_x, offset_y = fit_image_to_area(
        image=image,
        target_width=card_width,
        target_height=art_height,
        scale=scale,
    )

    # Create background (white or color palette)
    if color_bottom:
        # Extract colors from the original image
        analysis_image = resize_for_analysis(image, sample_size)
        colors = extract_top_five_colors(analysis_image)
        background = create_palette_strip(colors, card_width, card_height)
    else:
        background = Image.new("RGB", (card_width, card_height), (255, 255, 255))

    # Paste artwork at the top
    background.paste(artwork, (offset_x, 0))

    # Add RFID icon if requested
    if rfid is not None:
        rfid_path = Path(__file__).parent / f"rfid_{rfid}.png"
        if rfid_path.exists():
            rfid_icon = Image.open(rfid_path).convert("RGBA")
            
            # Scale to 75% of bottom area height
            target_height = round(bottom_height * 0.75)
            scale_factor = target_height / rfid_icon.height
            target_width = round(rfid_icon.width * scale_factor)
            rfid_icon = rfid_icon.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Position: horizontally centered, 3mm from bottom
            margin_3mm_px = round(3 / MM_PER_INCH * DPI_300)
            rfid_x = (card_width - target_width) // 2
            rfid_y = card_height - target_height - margin_3mm_px
            
            # Paste with transparency mask
            background.paste(rfid_icon, (rfid_x, rfid_y), rfid_icon)
        else:
            print(f"warning: RFID icon not found: {rfid_path}")

    if cutting_guide:
        draw_cutting_guide(background, corner_radius, bleed=bleed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.save(output_path)


def make_output_path(output_dir: Path, source_path: Path, suffix: str) -> Path:
    return output_dir / f"{source_path.stem}_{suffix}.png"


def resize_for_pdf(image: Image.Image, card_width_px: int, card_height_px: int, bleed: float) -> Image.Image:
    """Resize image for PDF, compensating for bleed margin."""
    bleed_px = round(bleed / MM_PER_INCH * DPI_300)
    
    if bleed > 0:
        # PNG size includes bleed on all sides
        effective_width = image.width - 2 * bleed_px
        effective_height = image.height - 2 * bleed_px
        scale_x = card_width_px / effective_width
        scale_y = card_height_px / effective_height
        scale_factor = min(scale_x, scale_y)
        target_width = round(image.width * scale_factor)
        target_height = round(image.height * scale_factor)
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    else:
        return image.resize((card_width_px, card_height_px), Image.Resampling.LANCZOS)


def create_pdf(
    front_path: Path,
    output_path: Path,
    back_path: Path | None = None,
    bleed: float = 0.0,
) -> None:
    """Create an A4 portrait PDF at 300 DPI with front and optionally back card images."""
    # Calculate dimensions at 300 DPI
    card_width_px = round(CARD_WIDTH_MM / MM_PER_INCH * DPI_300)
    card_height_px = round(CARD_HEIGHT_MM / MM_PER_INCH * DPI_300)
    a4_width_px = round(A4_WIDTH_MM / MM_PER_INCH * DPI_300)
    a4_height_px = round(A4_HEIGHT_MM / MM_PER_INCH * DPI_300)

    # Load and resize images
    front = Image.open(front_path).convert("RGB")
    front_scaled = resize_for_pdf(front, card_width_px, card_height_px, bleed)

    back_scaled = None
    if back_path:
        back = Image.open(back_path).convert("RGB")
        back_scaled = resize_for_pdf(back, card_width_px, card_height_px, bleed)

    # Create A4 page
    pdf_page = Image.new("RGB", (a4_width_px, a4_height_px), (255, 255, 255))

    # Center horizontally
    center_x = (a4_width_px - card_width_px) // 2
    margin_px = round(20 / MM_PER_INCH * DPI_300)  # 20mm margin

    if back_scaled is not None:
        # Two-sided: front on top, back on bottom
        front_y = margin_px
        back_y = margin_px + card_height_px + margin_px
        pdf_page.paste(front_scaled, (center_x, front_y))
        pdf_page.paste(back_scaled, (center_x, back_y))
    else:
        # Single-sided: center vertically
        center_y = (a4_height_px - card_height_px) // 2
        pdf_page.paste(front_scaled, (center_x, center_y))

    # Save as PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_page.save(output_path, "PDF", resolution=DPI_300)


def main() -> None:
    args = parse_args()
    validate_args(args)

    # Process front and back images
    images = [("front", args.front)]
    if args.back is not None:
        images.append(("back", args.back))

    outputs: dict[str, Path] = {}
    for side, input_path in images:
        output_path = make_output_path(args.output_dir, input_path, f"card_{side}")
        create_card_image(
            input_path=input_path,
            output_path=output_path,
            card_width=args.width,
            card_height=args.height,
            bottom_fraction=args.bottom_fraction,
            scale=args.scale,
            cutting_guide=args.cutting_guide,
            corner_radius=args.corner_radius,
            color_bottom=args.color_bottom,
            sample_size=args.sample_size,
            rfid=args.rfid,
            bleed=args.bleed,
        )
        print(f"saved: {output_path}")
        outputs[side] = output_path

    if args.pdf:
        pdf_output = args.output_dir / f"{args.front.stem}_card.pdf"
        create_pdf(outputs["front"], pdf_output, outputs.get("back"), args.bleed)
        print(f"saved: {pdf_output}")


if __name__ == "__main__":
    main()