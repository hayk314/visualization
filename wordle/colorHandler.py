# Author: Hayk Aleksanyan
# color related issued of word clouds are handled here

import random


def hslToRgb(h, s, l):
    """
       convert from HSL (hue-saturation-luminosity) to RGB format
       h, s, l are all in the range [0,1]
       r, g, b will be in the range [0,255]
       see https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
    """

    r, g, b =  0, 0, 0

    if s == 0:
        r, g, b = l, l, l
    else:
        def converter( p, q, t ):
            if t < 0:
                 t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                 return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = converter(p, q, h + 1/3)
        g = converter(p, q, h)
        b = converter(p, q, h - 1/3)

    return int(r * 255), int(g * 255), int(b * 255)


def getRandomColor():
    """
        return a random RGB triple which is not very bright as a color

        Note! bright colors need high saturation and high luminosity
        Note! lower saturation means grayish colors
    """

    h = random.random()
    s = random.random()

    if s > 0.8:
        s = 0.5
    l = random.random()
    if l > 0.5:
        #l = max(1 - l, 0.4)
        l = 0.5

    # s = 1
    # l = 0.5
    # s = 0

    return hslToRgb(h,s,l)

def colorTokens(normalTokens):
    # given a list of Tokens (see the wordle for Token class) we add their color attributes

    for token in normalTokens:
        token.color = getRandomColor()


def chooseFromFixedSchemes(normalTokens):
    # chose a color scheme based on the word frequency (fontSize)

    color_schemes = [
        [ (89, 97, 113), (115, 124, 140), (141, 150, 168), (179, 188, 204), (219, 227, 240) ],
        [ (89, 97, 113), (115, 124, 140), (141, 150, 168) , (89, 97, 113), (89, 97, 113)],
        [ (120, 120, 120), (0,100,149),  (242, 99, 95), (0, 76, 112), (244,208,12) ],
        [ (14, 38, 50), (1,70,99),  (35, 118, 150), (180, 200, 207), (159,195,185) ],
        [ (3, 113, 146), (99,167,190),  (10, 31, 78), (252, 105, 53), (252,105,53) ],
        [ (12, 6, 54), (9,81,105),  (5, 155, 154), (83, 186, 131), (159,217,107) ] ,
        [ (100, 101, 165), (105,117,167),  (244, 233, 109), (242, 138, 49), (241,88,56) ],
        [ (171, 165, 191), (90,87,118),  (88, 62, 47), (241, 224, 214), (191,153,144) ],
        [ (25, 46, 91), (30,101,167),  (115, 162, 192), (0, 116, 63), (241,161,4) ]
    ]

    # chose the color scheme randomly
    word_colors = color_schemes[ random.randint(0, len(color_schemes) - 1) ]
    max_size = max( [ token.fontSize for token in normalTokens ] )

    for token in normalTokens:
        if token.fontSize >= 0.7*max_size:
            c = word_colors[-1]
        elif ((token.fontSize >= 0.5*max_size)and(token.fontSize < 0.7*max_size) ):
            c = word_colors[-2]
        elif ((token.fontSize >= 0.35*max_size)and(token.fontSize < 0.5*max_size) ):
            c = word_colors[-3]
        elif ((token.fontSize >= 0.15*max_size)and(token.fontSize < 0.35*max_size) ):
            c = word_colors[-4]
        else:
            c = word_colors[-5]

        token.color = c
