import numpy as np
from PIL import Image
class Palette:
    def __init__(self, rgb_color_values):
        """Initializes a palette using the given list of RGB color values [r, g, b, ...]."""

        rgb_array = np.array(rgb_color_values, np.uint8).reshape((len(rgb_color_values) // 3, 3))
        self.num_colors = len(rgb_array)
        self.rgb = tuple(tuple(x) for x in rgb_array)
        self.lab = tuple(rgb_to_lab(x) for x in rgb_array)

    def get_nearest_color(self, rgb_color):
        """Returns a palette color that is most similar to the given color.""" 

        lab_color = rgb_to_lab(rgb_color)

        nearest_color_dist = np.inf
        nearest_color_index = 0
        for i in range(self.num_colors):
            dist = get_lab_distance(self.lab[i], lab_color)
            if dist < nearest_color_dist:
                nearest_color_dist = dist
                nearest_color_index = i

        return self.rgb[nearest_color_index]

def rgb_to_lab(rgb_color):
    """Converts the given RGB color to the CIELAB color space."""

    rgb = tuple(x / 255.0 for x in rgb_color)
    rgb = tuple(map(lambda x : pow((x + 0.055) / 1.055, 2.4) if x > 0.04045 else x / 12.92, rgb))

    xyz = ((rgb[0] * 41.24564 + rgb[1] * 35.75761 + rgb[2] * 18.04375) / 95.0489,
           (rgb[0] * 21.26729 + rgb[1] * 71.51522 + rgb[2] * 7.21750) / 100.0,
           (rgb[0] * 1.93339 + rgb[1] * 11.91920 + rgb[2] * 95.03041) / 108.884)
    xyz = tuple(map(lambda x : pow(x, 1.0 / 3) if x > 0.008856 else 7.78704 * x + 0.13793, xyz))

    return (116 * xyz[1] - 16, 500 * (xyz[0] - xyz[1]), 200 * (xyz[1] - xyz[2]))

def get_lab_distance(lab_color_0, lab_color_1):
    """Calculates a distance between two colors in the CIELAB color space using the CIE76 color difference formula."""

    v = np.subtract(lab_color_1, lab_color_0)
    return np.linalg.norm(v)

def get_palette(filename):
    """Returns a palette generated from the given image file."""

    palette_image = Image.open(filename)
    color_values = palette_image.getpalette()
    if color_values == None:
        raise Exception("The image does not have a palette") 

    return Palette(color_values)

def generate_lut(palette, size):
    """Returns a lookup table image generated from the given palette."""

    image = Image.new("RGBA", (size * size, size))

    for xyz in np.ndindex((size, size, size)):
        color = tuple(int(x * 256.0 / (size - 1)) for x in xyz)
        color_lightness = np.clip(int(rgb_to_lab(color)[0] / 100.0 * 255.0), 0, 255)
        nearest_color = palette.get_nearest_color(color)
        pos = (xyz[0] + xyz[2] * size, xyz[1])
        image.putpixel(pos, (*nearest_color, color_lightness))

    return image


palette = get_palette("palette-c64.png")
lut = generate_lut(palette, 64)
lut.save("color-grading.png")


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


lut = Image.open("color-grading.png")
test_image = Image.open("test.png")

for pos in np.ndindex((test_image.width, test_image.height)):
    color = test_image.getpixel(pos)
    color_lightness = get_lut_color(lut, color)[3]

    spread = np.clip(color_lightness * 2, 50, 150)
    threshold = get_dithering_threshold(pos)
    dithering_color = np.clip(np.add(color, spread * threshold), 0, 255)

    new_color = get_lut_color(lut, dithering_color)
    test_image.putpixel(pos, new_color)

test_image.save("test-palette.png")
