# Designed and implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

from PIL import Image, ImageColor, ImageFont, ImageDraw

import math
import random

import timeit   # for calculating running time (TESTING purposes only)
import sys


import fileReader as FR
import spirals as SP
import bbox
import Trees
from Trees import Node, Tree
import colorHandler as CH
from wordle import Token
import wordle

# constants:
TOKENS_TO_USE = 400       # number of different tokens to use in the wordle
STAY_AWAY = 2             # force any two words to stay at least this number of pixels away from each other
FONT_SIZE_MIN = 10        # the smallest font of a word
FONT_SIZE_MAX = 300       # the largest font of a word, might go slightly above this value
DESIRED_HW_RATIO = 0.618  # height/widht ratio of the canvas
QUADTREE_MINSIZE = 5      # minimal height-width of the box in quadTree partition
FONT_NAME = "arial.ttf"   # the font (true type) used to draw the word shapes


def proposeCanvasSize(normalTokens):
    """
      Given a list of normalized tokens we propose a canvase size (width, height)
      based on the areas covered by words. The areas are determined via leaves of the
      corresponding quadTrees.

      It is assumed that tokens come sorted (DESC), i.e. bigger sized words come first.
      We use this assumption when enforcing the canvas size to be larger
      than total area of the bounding boxes of the first few tokens.
    """

    area = 0         # the area covered by the quadTrees, i.e. the actual shape of the token
    boxArea = []     # the areas covered by the bounding box of the tokens

    for token in normalTokens:
        area += token.quadtree.area_covered()
        boxArea.append(Trees.rectArea(token.quadtree.root.value))

    ensure_space = 5    # force the sum of the total area to cover at least the first @ensure_space tokens

    total = area + sum ( boxArea[:ensure_space] )
    w = int( math.sqrt(total/DESIRED_HW_RATIO) ) + 1
    h = int(DESIRED_HW_RATIO*w) + 1

    print('Ratio of the area covered by trees over the total area of bounding boxes of words',  area/sum(boxArea))
    return w, h

def randomFlips(n, p):
    """
     Return an array of length n of random bits {0, 1} where Probability(0) = p and Probability(1) = 1 - p
     this is used for randomly selecting some of the tokens for vertical placement.
    """

    ans = n*[0]
    for i in range(n):
        x = random.random()
        if x > p:
            ans[i] = 1

    return ans



def normalizeWordSize(tokens, freq, N_of_tokens_to_use, horizontalProbability = 1.0):
    """
     (linearly) scale the font sizes of tokens to a new range depending on the ratio of the current min-max
     and take maximum @N_of_tokens_to_use of these tokens
     allow some words to have vertical orientation defined by @horizontalProbability
    """

    words = tokens[:N_of_tokens_to_use]
    sizes = freq[:N_of_tokens_to_use]

    normalTokens = [ ] # the list of Tokens to be returned

    # scale the range of sizes; the scaling rules applied below are fixed from some heuristic considerations
    # the user of this code is welcome to apply their own reasoning

    a, b = min(sizes), max(sizes)
    print( '\nThe ratio of MAX font-size over MIN equals ',  b/a  )
    if a == b:
        sizes = len(sizes)*[30]
    else:
        if b <= 8*a:
            m, M = 15, 1 + int(20*b/a)
        elif b <= 16*a:
            m, M = 14, 1 + int(18*b/a)
        elif b <= 32*a:
            m, M = 13, 1 + int(9*b/a)
        elif b <= 64*a:
            m, M = 11, 1 + int(4.7*b/a)
        else:
            m, M = FONT_SIZE_MIN, FONT_SIZE_MAX

        sizes = [  int(((M - m )/(b - a))*( x - a ) + m )  for x in sizes ]

    print( 'after scaling of fonts min = {}, max = {} '.format( min(sizes), max(sizes) ), '\n'  )


    # allow some vertical placement; the probability is defined by the user
    flips = randomFlips(len( words ), horizontalProbability )
    for i in range(len(sizes)):
        normalTokens.append( Token( words[i], sizes[i], 0 if flips[i] == 0 else 90 ) )


    return normalTokens


def drawOnCanvas(normalTokens, canvas_size):
    """
       given a list of tokens and a canvas size, we put the token images onto the canvas
       the places of each token on this canvas has already been determined during placeWords() call.

       Notice, that it is not required that the @place of each @token is inside the canvas;
       if necessary we may enlarge the canvas size to embrace these missing images
    """

    c_W,c_H = canvas_size        # the suggested canvas size, might change here

    # there can be some positions of words which fell out of the canvas
    # we first need to go through these exceptions (if any) and expand the canvas and (or) shift the coordinate's origin.

    X_min, Y_min = 0, 0

    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        if X_min > token.place[0]:  X_min = token.place[0]
        if Y_min > token.place[1]:  Y_min = token.place[1]

    x_shift, y_shift = 0, 0
    if X_min < 0:   x_shift = -X_min
    if Y_min < 0:   y_shift = -Y_min

    X_max , Y_max = 0, 0
    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        token.place = ( token.place[0] + x_shift, token.place[1] + y_shift )
        if X_max < token.place[0] + token.img_size[0]:
            X_max = token.place[0] + token.img_size[0]
        if Y_max < token.place[1] + token.img_size[1]:
            Y_max = token.place[1] + token.img_size[1]

    c_W = max(c_W, X_max)
    c_H = max(c_H, Y_max)

    im_canvas = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = None )
    im_canvas_white = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = (255,255,255,255) )

    # decide the background color with a coin flip; 0 -for white; 1 - for black (will need brigher colors)
    background = random.randint(0,1)

    dd = ImageDraw.Draw(im_canvas)
    if background == 0: # white
        dd_white = ImageDraw.Draw(im_canvas_white)


    # add color to each word to be placed on canvas, pass on the background info as well
    CH.colorTokens(normalTokens, background)

    for i, token in enumerate(normalTokens):
        if token.place == None:
            print('the word <' + token.word + '> was skipped' )
            continue

        font1 = ImageFont.truetype(FONT_NAME, token.font_size)
        c = token.color

        if token.draw_at_angle != 0:
            # place vertically, since PIL does support drawing text in vertical orientation,
            # we first draw the token in a temporary image, the @im, then past that at the location of
            # the token on the canvas; this might introduce some rasterization for smaller fonts
            im = wordle.draw_word(token, useColor = True)
            im_canvas.paste(im,  token.place, im )
            if background == 0:
                im_canvas_white.paste(im,  token.place, im )
        else:
            dd.text( token.place, token.word, fill = c,  font = font1 )
            if background == 0:
                dd_white.text( token.place, token.word, fill = c,  font = font1 )


    margin_size = 10 # the border margin size
    box = im_canvas.getbbox()

    if background == 0:
        im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
        im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )
    else:
        im_canvas_1 = Image.new('RGB', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (0,0,0)  )
        im_canvas_1.paste( im_canvas.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1



def createWordle_fromFile( fName, interActive = False, horizontalProbability = 1.0 ):
    # the master function, creates the wordle from a given text file

    tokens = FR.tokenize_file_IntoWords(fName)
    tokens, freq = FR.tokenGroup(tokens)

    print('\n ===== Top', min(10, len(tokens) ),  'most frequent tokens =====\n')

    for i in range(  min(10, len(tokens) ) ):
        s = freq[i]
        print( str(s) +  (7 - len(str(s)))*' ' + ':  ' + tokens[i]  )


    normalTokens =  normalizeWordSize(tokens, freq, TOKENS_TO_USE, horizontalProbability)
    canvas_W, canvas_H = wordle.place_words(normalTokens)

    wordle_img = drawOnCanvas(normalTokens, (canvas_W, canvas_H ) )
    wordle_img.save( fName[0:-4] + '_wordle.png')
    print( 'the wordle image was sucessfully saved on the disc as <' + fName[0:-4]  + '_wordle.png >' )

    if interActive == True:
        # we allow the user to repaint the existing tokens with other color schemes as many times as they wish
        print('\n=========== You may repaint the existing wordle with other color schemes =========== \n')
        print('To stop, please type the text inside the quotes: "q" folowed by Enter')
        print('To try a new scheme type any other char\n')

        version = 1
        while True:
            userInput = input(str(version) + '.   waiting for new user input ... ')
            if userInput == 'q':
                print('exiting...')
                break
            wordle_img = drawOnCanvas(normalTokens, (canvas_W, canvas_H))
            newFileName = fName[0:-4] + '_wordle_v' + str(version) + '.png'
            wordle_img.save( newFileName)
            print( '=== saved on the disc as <', newFileName, '>\n')
            version += 1



if __name__ == "__main__":
    # waits for .txt fileName and interactive flag {0, 1} for processing

    interActive = False        # if True, keep repainting the wordle on user's demand
    verticalProbability = 0    # the probability of placing some words vertically

    if len(sys.argv) > 2 and sys.argv[2] == '1':
        interActive = True
    if len(sys.argv) > 3:
        try:
            verticalProbability = float(sys.argv[3])
            if verticalProbability > 1: verticalProbability = 1.0
            if verticalProbability < 0: verticalProbability = 0.0
        except:
            verticalProbability = 0.0


    createWordle_fromFile( sys.argv[1], interActive, 1 - verticalProbability )
