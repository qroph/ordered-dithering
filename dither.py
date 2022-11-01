import sys
import numpy as np
from PIL import Image


dithering_matrix = tuple((x / 64.0) - 0.5 for x in (
     0, 32,  8, 40,  2, 34, 10, 42,
    48, 16, 56, 24, 50, 18, 58, 26,
    12, 44,  4, 36, 14, 46,  6, 38,
    60, 28, 52, 20, 62, 30, 54, 22,
     3, 35, 11, 43,  1, 33,  9, 41,
    51, 19, 59, 27, 49, 17, 57, 25,
    15, 47,  7, 39, 13, 45,  5, 37,
    63, 31, 55, 23, 61, 29, 53, 21
))


def get_dithering_threshold(pos):
    """Returns a dithering threshold for the given position."""

    x = int(pos[0]) % 8
    y = int(pos[1]) % 8
    return dithering_matrix[x + y * 8]


def get_lut_color(lut, color):
    """Returns a value from the given lookup table for the given color."""

    size = lut.height
    rgb = np.floor(np.divide(color, 256.0) * size)
    x = rgb[0] + rgb[2] * size + 0.5 / lut.width
    y = rgb[1] + 0.5 / lut.height
    return lut.getpixel((x, y))


def dither_image(image, lut):
    """Dithers the given image using the given lookup table."""

    output = Image.new("RGB", image.size)

    for pos in np.ndindex((image.width, image.height)):
        color = image.getpixel(pos)
        color_lightness = get_lut_color(lut, color)[3]

        spread = 0.5 * color_lightness # This value can be tweaked
        threshold = get_dithering_threshold(pos)
        dithering_color = np.clip(np.add(color, spread * threshold), 0, 255)

        new_color = get_lut_color(lut, dithering_color)
        output.putpixel(pos, new_color)

    return output


def main(argv):
    if len(argv) != 3:
        print("usage: dither.py image_filename lut_filename output_filename")
        sys.exit(2)

    image = Image.open(argv[0]).convert("RGB")
    lut = Image.open(argv[1])
    output = dither_image(image, lut)
    output.save(argv[2])


if __name__ == "__main__":
   main(sys.argv[1:])
