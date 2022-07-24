import numpy as np
from PIL import Image
class Palette:
    def __init__(self, rgb_colors):
        self.num_colors = len(rgb_colors)
        self.rgb = list(map(lambda x : tuple(x), rgb_colors))
        self.lab = list(map(lambda x : rgb_to_lab(x), self.rgb))
        self.nearest_darker_color_indices = [i for i in range(self.num_colors)]
        self.nearest_lighter_color_indices = [i for i in range(self.num_colors)]

        for j in range(self.num_colors):
            nearest_darker_color_dist = np.inf
            nearest_lighter_color_dist = np.inf
            for i in range(self.num_colors):
                if self.lab[i][0] < self.lab[j][0]:
                    dist = get_lab_distance(self.lab[i], self.lab[j])
                    if dist < nearest_darker_color_dist:
                        nearest_darker_color_dist = dist
                        self.nearest_darker_color_indices[j] = i
                elif self.lab[i][0] > self.lab[j][0]:
                    dist = get_lab_distance(self.lab[i], self.lab[j])
                    if dist < nearest_lighter_color_dist:
                        nearest_lighter_color_dist = dist
                        self.nearest_lighter_color_indices[j] = i

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

        return [self.rgb[nearest_color_index],
            self.rgb[second_nearest_color_index],
            self.rgb[self.nearest_darker_color_indices[nearest_color_index]],
            self.rgb[self.nearest_lighter_color_indices[nearest_color_index]]]

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
    image = Image.new("RGB", (res * res, 5 * res))
    step = 256.0 / (res - 1)
    for r, g, b in np.ndindex((res, res, res)):
        color = (int(r * step), int(g * step), int(b * step))
        nearest_colors = palette.get_nearest_colors(color)
        image.putpixel((r + b * res, g), nearest_colors[0])
        image.putpixel((r + b * res, g + res), nearest_colors[1])
        image.putpixel((r + b * res, g + 2 * res), nearest_colors[2])
        image.putpixel((r + b * res, g + 3 * res), nearest_colors[3])
        image.putpixel((r + b * res, g + 4 * res), color)

    return image


lut_res = 32
#palette = get_palette("palette-C64.png")
#lut = generate_lut(palette, lut_res)
#lut.save("color-grading.png")


lut = Image.open("color-grading.png")

def get_lut_color(lut, color, row, res):
    r = color[0] / 256.0
    g = color[1] / 256.0
    b = color[2] / 256.0
    cell = np.floor(b * res)
    x = np.floor(r * res) + cell * res + 0.5 / lut.width
    y = np.floor(g * res) + row * res + 0.5 / lut.height
    return lut.getpixel((x, y))

test_image = Image.open("test.png")
for pos in np.ndindex((test_image.width, test_image.height)):
    old_color = test_image.getpixel(pos)
    nearest_color = get_lut_color(lut, old_color, 0, lut_res)
    second_nearest_color = get_lut_color(lut, old_color, 1, lut_res)
    test_image.putpixel(pos, second_nearest_color)

test_image.save("test-palette.png")
