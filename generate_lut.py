import sys
import numpy as np
from PIL import Image


class Palette:
    def __init__(self, rgb_color_values, distance_func):
        """Initializes a palette using the given list of RGB color values [r, g, b, ...]."""

        rgb_array = np.array(rgb_color_values, np.uint8).reshape((len(rgb_color_values) // 3, 3))
        self.num_colors = len(rgb_array)
        self.rgb = tuple(tuple(x) for x in rgb_array)
        self.lab = tuple(rgb_to_lab(x) for x in rgb_array)
        self.get_lab_distance = distance_func


    def get_nearest_color(self, rgb_color):
        """Returns a palette color that is most similar to the given color.""" 

        lab_color = rgb_to_lab(rgb_color)

        nearest_color_dist = np.inf
        nearest_color_index = 0
        for i in range(self.num_colors):
            dist = self.get_lab_distance(lab_color, self.lab[i])
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


def get_lab_distance_CIE76(lab_color_0, lab_color_1):
    """Calculates a distance between two colors in the CIELAB color space using the CIE76 color difference formula."""

    v = np.subtract(lab_color_1, lab_color_0)
    return np.linalg.norm(v)


def get_lab_distance_CIE94(lab_color_0, lab_color_1):
    """Calculates a distance between two colors in the CIELAB color space using the CIE94 color difference formula."""

    C1 = np.sqrt(lab_color_0[1]**2 + lab_color_0[2]**2)
    C2 = np.sqrt(lab_color_1[1]**2 + lab_color_1[2]**2)
    dC = C1 - C2

    (dL, da, db) = np.subtract(lab_color_0, lab_color_1)
    dH = np.sqrt(max(0, da**2 + db**2 - dC**2))

    return np.sqrt(dL**2 + pow(dC / (1 + 0.045 * C1), 2) + pow(dH / (1 + 0.015 * C1), 2))


def get_lab_distance_CIEDE2000(lab_color_0, lab_color_1):
    """Calculates a distance between two colors in the CIELAB color space using the CIEDE2000 color difference formula."""

    (L1, a1, b1) = lab_color_0
    (L2, a2, b2) = lab_color_1

    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)

    t = 0.5 * (C1 + C2)
    mult = np.sqrt(t**7 / (t**7 + 25**7))

    t = 1 + 0.5 * (1 - mult)
    a1_ = t * a1
    a2_ = t * a2

    C1_ = np.sqrt(a1_**2 + b1**2)
    C2_ = np.sqrt(a2_**2 + b2**2)
    C1_C2_ = C1_ * C2_

    h1_ = 0 if C1_ == 0 else np.rad2deg(np.arctan2(b1, a1_)) % 360
    h2_ = 0 if C2_ == 0 else np.rad2deg(np.arctan2(b2, a2_)) % 360

    dh_ = 0 if C1_C2_ == 0 else \
        h2_ - h1_ if abs(h1_ - h2_) <= 180 else \
        h2_ - h1_ + 360 if h2_ <= h1_ else \
        h2_ - h1_ - 360

    dH_ = 2 * np.sqrt(C1_C2_) * np.sin(np.deg2rad(0.5 * dh_))

    H_average = h1_ + h2_ if C1_C2_ == 0 else \
        0.5 * (h1_ + h2_) if abs(h1_ - h2_) <= 180 else \
        0.5 * (h1_ + h2_ + 360) if h1_ + h2_ < 360 else \
        0.5 * (h1_ + h2_ - 360)

    T = 1 - \
        0.17 * np.cos(np.rad2deg(H_average - 30)) + \
        0.24 * np.cos(np.rad2deg(2 * H_average)) + \
        0.32 * np.cos(np.rad2deg(3 * H_average + 6)) - \
        0.20 * np.cos(np.rad2deg(4 * H_average - 63))

    t = pow(0.5 * (L1 + L2) - 50, 2)
    SL = 1 + 0.015 * t / np.sqrt(20 + t)

    t = 0.5 * (C1_ + C2_)
    SC = 1 + 0.045 * t
    SH = 1 + 0.015 * t * T

    RT = -2 * mult * np.sin(np.deg2rad(60 * np.exp(-pow((H_average - 275) / 25, 2))))

    dL = L2 - L1
    dC_ = C2_ - C1_
    return np.sqrt((dL / SL)**2 + (dC_ / SC)**2 + (dH_ / SH)**2 + RT * dC_ * dH_ / (SC * SH))


def get_palette(filename, distance_func):
    """Returns a palette generated from the given image file."""

    palette_image = Image.open(filename)
    color_values = palette_image.getpalette()
    if color_values == None:
        raise Exception("The image does not have a palette") 

    return Palette(color_values, distance_func)


def generate_lut(palette, size, min_spread, max_spread):
    """Returns a lookup table image generated from the given palette."""

    image = Image.new("RGBA", (size * size, size))

    for xyz in np.ndindex((size, size, size)):
        color = tuple(int(x * 256.0 / (size - 1)) for x in xyz)
        color_lightness = rgb_to_lab(color)[0] / 100.0
        nearest_color = palette.get_nearest_color(color)

        # This value can be tweaked
        spread = min_spread + (max_spread - min_spread) * (1 - (2 * color_lightness - 1)**4);

        pos = (xyz[0] + xyz[2] * size, xyz[1])
        image.putpixel(pos, (*nearest_color, int(spread)))

    return image


def main(argv):
    if len(argv) != 3 and len(argv) != 4 and len(argv) != 6:
        print("usage: generate_lut.py palette_filename output_filename lut_size [color_distance_formula] [min_spread max_spread]")
        sys.exit(2)

    formula = argv[3] if len(argv) >= 4 else ""
    distance_func = \
        get_lab_distance_CIE76 if formula == "CIE76" else \
        get_lab_distance_CIE94 if formula == "CIE94" else \
        get_lab_distance_CIEDE2000

    min_spread = int(argv[4]) if len(argv) == 6 else 0
    max_spread = int(argv[5]) if len(argv) == 6 else 120

    palette = get_palette(argv[0], distance_func)
    lut = generate_lut(palette, int(argv[2]), min_spread, max_spread)
    lut.save(argv[1])


if __name__ == "__main__":
   main(sys.argv[1:])
