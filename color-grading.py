import numpy as np
from PIL import Image
class Palette:
    def __init__(self, rgb_colors):
        self.num_colors = len(rgb_colors)
        self.rgb = list(map(lambda x : tuple(x), rgb_colors))
        self.lab = list(map(lambda x : rgb_to_lab(x), self.rgb))

    def get_nearest_colors(self, color):
        lab_color = rgb_to_lab(color)

        nearest_color_dist = np.inf
        nearest_color_index = 0
        second_nearest_color_dist = np.inf
        second_nearest_color_index = 0

        for i in range(self.num_colors):
            dist = get_lab_distance(self.lab[i], lab_color)
            if dist < nearest_color_dist:
                second_nearest_color_dist = nearest_color_dist
                second_nearest_color_index = nearest_color_index
                nearest_color_dist = dist
                nearest_color_index = i
            elif dist < second_nearest_color_dist:
                second_nearest_color_dist = dist
                second_nearest_color_index = i

        return (self.rgb[nearest_color_index], self.rgb[second_nearest_color_index])

def rgb_to_lab(color):
    r = color[0] / 255.0
    g = color[1] / 255.0
    b = color[2] / 255.0

    if r > 0.04045:
        r = pow((r + 0.055) / 1.055, 2.4)
    else:
        r /= 12.92
    if g > 0.04045:
        g = pow((g + 0.055) / 1.055, 2.4)
    else:
        g /= 12.92
    if b > 0.04045:
        b = pow((b + 0.055) / 1.055, 2.4)
    else:
        b /= 12.92

    x = (r * 41.24564 + g * 35.75761 + b * 18.04375) / 95.0489
    y = (r * 21.26729 + g * 71.51522 + b * 7.21750) / 100.0
    z = (r * 1.93339 + g * 11.91920 + b * 95.03041) / 108.884

    if x > 0.008856:
        x = pow(x, 1.0 / 3)
    else:
        x = 7.78704 * x + 0.13793
    if y > 0.008856:
        y = pow(y, 1.0 / 3)
    else:
        y = 7.78704 * y + 0.13793
    if z > 0.008856:
        z = pow(z, 1.0 / 3)
    else:
        z = 7.78704 * z + 0.13793

    return (116 * y - 16, 500 * (x - y), 200 * (y - z))

def get_lab_distance(lab_color_0, lab_color_1):
    v = np.subtract(lab_color_1, lab_color_0)
    return np.linalg.norm(v)

def get_palette(filename):
    palette_image = Image.open(filename)
    rgb_colors = palette_image.getpalette()
    rgb_colors = np.array(rgb_colors, np.uint8).reshape((len(rgb_colors) // 3, 3))
    return Palette(rgb_colors)

def generate_lut(palette, res):
    image = Image.new("RGB", (res * res, 2 * res))
    step = 256.0 / (res - 1)
    for r, g, b in np.ndindex((res, res, res)):
        color = (int(r * step), int(g * step), int(b * step))
        nearest_colors = palette.get_nearest_colors(color)
        image.putpixel((r + b * res, g), nearest_colors[0])
        image.putpixel((r + b * res, g + res), nearest_colors[1])

    return image


lut_res = 64
#palette = get_palette("palette-c64.png")
#lut = generate_lut(palette, lut_res)
#lut.save("color-grading.png")


dither_matrix = [
    0,  32, 8,  40, 2,  34, 10, 42,
    48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4,  36, 14, 46, 6,  38,
    60, 28, 52, 20, 62, 30, 54, 22,
    3,  35, 11, 43, 1,  33, 9,  41,
    51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7,  39, 13, 45, 5,  37,
    63, 31, 55, 23, 61, 29, 53, 21]

def get_dither_threshold(pos):
    x = int(pos[0]) % 8
    y = int(pos[1]) % 8
    return dither_matrix[x + y * 8] / 64.0

def get_lut_color(lut, color, row, res):
    r = color[0] / 256.0
    g = color[1] / 256.0
    b = color[2] / 256.0
    cell = np.floor(b * res)
    x = np.floor(r * res) + cell * res + 0.5 / lut.width
    y = np.floor(g * res) + row * res + 0.5 / lut.height
    return lut.getpixel((x, y))


lut = Image.open("color-grading.png")
test_image = Image.open("test.png")

def color_diff(color0, color1):
    d = np.subtract(np.array(color0), np.array(color1))
    d = np.divide(d, 255.0)
    return np.sqrt(d[0]**2 * 0.299 + d[1]**2 * 0.587 + d[2]**2 * 0.114)

for pos in np.ndindex((test_image.width, test_image.height)):
    spread = 128.0
    threshold = get_dither_threshold(pos) - 0.5

    old_color = test_image.getpixel(pos)
    dither_color = np.clip(np.add(old_color, spread * threshold), 0, 255)
    c0 = get_lut_color(lut, dither_color, 0, lut_res)
    c1 = get_lut_color(lut, dither_color, 1, lut_res)
    new_color = c0 if color_diff(old_color, c0) < color_diff(old_color, c1) else c1

    test_image.putpixel(pos, new_color)

test_image.save("test-palette.png")
