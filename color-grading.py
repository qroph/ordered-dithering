import sys
from xml.dom import INDEX_SIZE_ERR
import numpy as np
from PIL import Image

def get_palette(filename):
    palette_image = Image.open(filename)
    palette = palette_image.getpalette()
    palette = np.array(palette, np.uint8).reshape((len(palette) // 3, 3))
    return list(map(lambda x : tuple(x), palette))

# def get_palette_colors(color: Color) -> Array:
#     var nearest_colors := [null, null]
#     var nearest_color_dists := [1000000.0, 1000000.0]

#     for j in palette.get_height():
#         for i in palette.get_width():
#             var palette_color := palette.get_pixel(i, j)
#             var dist := get_distance(color, palette_color)
#             if dist < nearest_color_dists[0]:
#                 nearest_color_dists[1] = nearest_color_dists[0]
#                 nearest_color_dists[0] = dist
#                 nearest_colors[1] = nearest_colors[0]
#                 nearest_colors[0] = palette_color
#             elif dist < nearest_color_dists[1]:
#                 nearest_color_dists[1] = dist
#                 nearest_colors[1] = palette_color

#     return nearest_colors

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

def get_nearest_colors(palette, color):
    def get_distance(c0, c1):
        v = np.subtract(rgb_to_lab(c1), rgb_to_lab(c0))
        return np.linalg.norm(v)

    dark_color_indices = [i for i in range(len(palette))]
    light_color_indices = dark_color_indices

    nearest_color_dist = sys.float_info.max
    nearest_color_index = 0
    for i in range(len(palette)):
        dist = get_distance(palette[i], color)
        if dist < nearest_color_dist:
            nearest_color_dist = dist
            nearest_color_index = i

    nearest_colors = []
    nearest_colors.append(palette[nearest_color_index])
    nearest_colors.append(palette[dark_color_indices[nearest_color_index]])
    nearest_colors.append(palette[light_color_indices[nearest_color_index]])

    return nearest_colors

def generate_lut(palette, res):
    image = Image.new("RGB", (res * res, 4 * res))
    step = 256.0 / (res - 1)
    for r, g, b in np.ndindex((res, res, res)):
        color = (int(r * step), int(g * step), int(b * step))
        nearest_colors = get_nearest_colors(palette, color)
        image.putpixel((r + b * res, g), nearest_colors[0])
        image.putpixel((r + b * res, g + res), nearest_colors[1])
        image.putpixel((r + b * res, g + 2 * res), nearest_colors[2])
        image.putpixel((r + b * res, g + 3 * res), color)

    return image

palette = get_palette("palette-C64.png")
lut = generate_lut(palette, 32)
lut.save("color-grading.png")
