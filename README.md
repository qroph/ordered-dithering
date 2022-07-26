# Ordered dithering

This repository contains an implementation of ordered dithering that works with custom palettes.

Two Python 3 scripts are included. The first is `generate_lut.py`, which generates a lookup table for a given palette. The second is `dither.py`, which uses a previously generated lookup table and dithers a given image using it. The scripts require NumPy and Pillow to be installed.

The actual dithering algorithm is very fast when it uses a pre-built lookup table. It handles each pixel individually, and therefore the algorithm is also very easy to implement in a shader to achieve real-time dithering.

## Examples

Here are some example images that have been dithered using this algorithm. All examples use the Commodore 64 palette (https://lospec.com/palette-list/commodore64).

![Commodore 64 palette](/examples/palette.png)

![Parrot](/examples/parrot.jpg) ![Dithered Parrot](/examples/parrot_dithered.png)

![Lenna](/examples/lenna.png) ![Dithered Lenna](/examples/lenna_dithered.png)

![RGB](/examples/rgb.png) ![Dithered RGB](/examples/rgb_dithered.png)

