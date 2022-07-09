import sys
import numpy as np
from PIL import Image

def get_palette(filename):
    palette_image = Image.open(filename)
    palette = palette_image.getpalette()
    palette = np.array(palette, np.uint8).reshape((len(palette) // 3, 3))
    return list(map(lambda x : tuple(x), palette))

def get_distance(c0, c1):
    v = np.subtract(np.array(rgb_to_lab(c1)), np.array(rgb_to_lab(c0)))
    return np.linalg.norm(v)

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
    z = (r * 1.93339 + g * 11.91920 + b * 95.03041) / 108.8840

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

def get_nearest_colors(palette, color):
    nearest_color = (0, 0, 0)
    nearest_color_dist = sys.float_info.max
    for palette_color in palette:
        distance = get_distance(palette_color, color)
        if distance < nearest_color_dist:
            nearest_color_dist = distance
            nearest_color = palette_color

    return (nearest_color, nearest_color)

def generate_lookup_image(palette, res):
    image = Image.new("RGB", (res * res, 2 * res))
    step = 256.0 / (res - 1)
    for r, g, b in np.ndindex((res, res, res)):
        color = (int(r * step), int(g * step), int(b * step))
        nearest_colors = get_nearest_colors(palette, color)
        image.putpixel((r + b * res, g), color)#nearest_colors[0])
        image.putpixel((r + b * res, g + res), nearest_colors[1])

    return image

palette = get_palette("palette-1.png")
lookup_image = generate_lookup_image(palette, 32)
lookup_image.save("color-grading.png")
