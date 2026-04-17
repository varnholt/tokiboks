#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract 5 dominant colors from an image and create a Kuler-style palette strip."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="input image file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output image file (default: <input>_kuler.png)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1000,
        help="output width in pixels (default: 1000)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=200,
        help="output height in pixels (default: 200, giving a 5:1 ratio with the default width)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="resize longer side to this many pixels before analysis (default: 300)",
    )
    return parser.parse_args()


def resize_for_analysis(image: Image.Image, sample_size: int) -> Image.Image:
    width, height = image.size

    if width >= height:
        new_width = sample_size
        new_height = max(1, int(height * sample_size / width))
    else:
        new_height = sample_size
        new_width = max(1, int(width * sample_size / height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


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


def create_palette_image(
    colors: list[tuple[int, int, int]],
    width: int,
    height: int,
) -> Image.Image:
    palette_image = Image.new("RGB", (width, height), (255, 255, 255))

    box_width = width // 5

    for index, color in enumerate(colors):
        left = index * box_width
        right = (index + 1) * box_width if index < 4 else width

        box = Image.new("RGB", (right - left, height), color)
        palette_image.paste(box, (left, 0))

    return palette_image


def main() -> None:
    args = parse_args()

    if args.width <= 0 or args.height <= 0:
        raise ValueError("width and height must be positive integers")

    if not args.input_file.is_file():
        raise FileNotFoundError(f"input file not found: {args.input_file}")

    output_file = args.output
    if output_file is None:
        output_file = args.input_file.with_name(f"{args.input_file.stem}_kuler.png")

    image = Image.open(args.input_file).convert("RGB")
    analysis_image = resize_for_analysis(image, args.sample_size)
    colors = extract_top_five_colors(analysis_image)
    palette_image = create_palette_image(colors, args.width, args.height)

    palette_image.save(output_file)
    print(f"saved: {output_file}")


if __name__ == "__main__":
    main()