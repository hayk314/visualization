# Author: Hayk Aleksanyan
# color related aspects of word clouds are handled here

import random


def convert_hsl_to_rgb(h, s, l):
    """
       convert from HSL (hue-saturation-luminosity) to RGB format
       h, s, l are all in the range [0,1]
       r, g, b will be in the range [0,255]
       see https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
    """

    if s == 0:
        r, g, b = l, l, l
    else:
        def converter(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = converter(p, q, h + 1 / 3)
        g = converter(p, q, h)
        b = converter(p, q, h - 1 / 3)

    return int(r * 255), int(g * 255), int(b * 255)


def get_random_color(h=-1, s=-1, l=-1, bright=False):
    """
        return a random RGB triple which is not very bright as a color, if @bright == False; and is bright otherwise
        we allow for some of the components of the HSL be predefined, and others being chosen at random
        to fix the specific HSL coordinate change the -1 value to the one you wish from interval [0,1]

        Note ==>  bright colors need high saturation and high luminosity
        Note ==>  lower saturation means grayish colors
    """

    if h == -1 or not 0 <= h <= 1:
        h = random.random()
    if s == -1 or not 0 <= s <= 1:
        s = random.random()
        if not bright:
            if s > 0.8:
                s = 0.5
        else:
            if s < 0.5:
                s = 1 - s

    if l == -1 or not 0 <= l <= 1:
        l = random.random()
        if not bright:
            if l > 0.5:
                l = 1 - l
        else:
            if l < 0.5:
                l = 1 - l

    return convert_hsl_to_rgb(h, s, l)


def add_color_to_tokens(normal_tokens, background=0):
    """
      given a list of Tokens (see the wordle for Token class) we add their color attributes
      @background == 0 means WHITE; == 1 means Black background, needs brighter colors
      by picking a random color scheme and applying on the Tokens
    """

    if background == 0:
        scheme = random.randint(0, 3)
        if scheme == 0:
            print('\nColor scheme: Random\n')
            add_random_color_to_tokens(normal_tokens)
        elif scheme == 1:
            print('\nColor scheme: Jet\n')
            add_jet_colors(normal_tokens)
        elif scheme == 2:
            print('\nColor scheme: Grayish\n')
            add_grayish_random_colors(normal_tokens)
        elif scheme == 3:
            print('\nColor scheme: From a fixed list\n')
            add_color_from_fixed_schemes(normal_tokens)
    else:
        print('\nColor scheme: Random, black background\n')
        add_random_color_to_tokens(normal_tokens, background=1)


def add_random_color_to_tokens(normal_tokens, background=0):
    """ apply random colors of slightly darker gamma on white background == 0
        and bright colors on black background == 1
    """

    for token in normal_tokens:
        if background == 0:
            token.color = get_random_color()
        else:
            token.color = get_random_color(h=-1, s=-1, l=-1, bright=True)


def add_jet_colors(normalTokens):
    """ apply jet color (heatmap) scheme on tokens """
    if not normalTokens:
        return

    h, s, l = 0, 0.85, 0.4
    step = 0.7 / len(normalTokens)

    for token in normalTokens:
        token.color = convert_hsl_to_rgb(h, s, l)
        h += step


def add_grayish_random_colors(normal_tokens):
    """ apply grayscale random colors """
    for token in normal_tokens:
        # get a random color with lower saturation, this will ensure a grayish color
        token.color = get_random_color(h=-1, s=0, l=-1)


def add_color_from_fixed_schemes(normal_tokens):
    """ choose a color scheme from a fixed list which colors tokens based on the fontSize """

    color_schemes = [
        [(89, 97, 113), (115, 124, 140), (141, 150, 168), (179, 188, 204), (219, 227, 240)],
        [(89, 97, 113), (115, 124, 140), (141, 150, 168), (89, 97, 113), (89, 97, 113)],
        [(120, 120, 120), (0, 100, 149), (242, 99, 95), (0, 76, 112), (244, 208, 12)],
        [(14, 38, 50), (1, 70, 99), (35, 118, 150), (180, 200, 207), (159, 195, 185)],
        [(3, 113, 146), (99, 167, 190), (10, 31, 78), (252, 105, 53), (252, 105, 53)],
        [(12, 6, 54), (9, 81, 105), (5, 155, 154), (83, 186, 131), (159, 217, 107)],
        [(100, 101, 165), (105, 117, 167), (244, 233, 109), (242, 138, 49), (241, 88, 56)],
        [(171, 165, 191), (90, 87, 118), (88, 62, 47), (241, 224, 214), (191, 153, 144)],
        [(25, 46, 91), (30, 101, 167), (115, 162, 192), (0, 116, 63), (241, 161, 4)]
    ]

    # chose the color scheme randomly
    word_colors = color_schemes[random.randint(0, len(color_schemes) - 1)]
    max_size = max([token.font_size for token in normal_tokens])

    for token in normal_tokens:
        if token.font_size >= 0.7 * max_size:
            c = word_colors[-1]
        elif (token.font_size >= 0.5 * max_size) and (token.font_size < 0.7 * max_size):
            c = word_colors[-2]
        elif (token.font_size >= 0.35 * max_size) and (token.font_size < 0.5 * max_size):
            c = word_colors[-3]
        elif (token.font_size >= 0.15 * max_size) and (token.font_size < 0.35 * max_size):
            c = word_colors[-4]
        else:
            c = word_colors[-5]

        token.color = c
