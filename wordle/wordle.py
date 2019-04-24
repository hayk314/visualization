# Implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

from PIL import Image, ImageColor, ImageFont, ImageDraw

import math     # for sin, cos
import random   # used for random placement of the initial position of a word

import timeit   # for calculating running time (TESTING purposes only)
import sys


import fileReader as FR
import spirals as SP
import BBox
import Trees
from Trees import Node, Tree
import colorHandler as CH

# constants:
TOKENS_TO_USE = 400       # number of different tokens to use in the wordle
STAY_AWAY = 2             # force any two words to stay at least this number of pixels away from each other
FONT_SIZE_MIN = 10        # the smallest font of a word
FONT_SIZE_MAX = 300       # the largest font of a word
DESIRED_HW_RATIO = 0.618  # height/widht ratio of the canvas
QUADTREE_MINSIZE = 5      # minimal height-width of the box in quadTree partition
FONT_NAME = "arial.ttf"   # the font (true type) used to draw the word shapes


class Token:
    """
        encapsulate the main information on a token into a single class
        Token here represents a word to be placed on canvas for the final wordle Image

        most of the attributes are filled with functions during processing of the tokens
    """

    def __init__(self, word, fontSize = 10, drawAngle = 0):
        self.word = word
        self.fontSize = fontSize      # an integer
        self.drawAngle = drawAngle    # an integer, representing the rotation angle of the image; 0 - for NO rotation
        self.imgSize = None           # tuple of integers (width, height)
        self.quadTree = None          # the quadTree of the image of this word with the above characteristics
        self.place = None             # tuple, the coordinate of the upper-left cordner of the token on the final canvas
        self.color = None             # the fill color on canvas (R, G, B) triple


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
        area += token.quadTree.areaCovered()
        boxArea.append( Trees.rectArea(token.quadTree.root.value) )

    ensure_space = 5    # force the sum of the total area to cover at least first @ensure_space tokens

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



def normalizeWordSize(tokens, freq, N_of_tokens_to_use, max_size, min_size):
    """
     (linearly) scale the font sizes of tokens to the range [min_size, max_size]
     and take maximum @N_of_tokens_to_use of these tokens
    """

    words = tokens[:N_of_tokens_to_use]
    sizes = freq[:N_of_tokens_to_use]

    normalTokens = [ ] # the list of Tokens to be returned

    # scale the range of sizes to the given range [min_size, max_size]
    a, b = min(sizes), max(sizes)
    sizes = [  int(((max_size - min_size )/(b - a))*( x - a ) + min_size )  for x in sizes ]

    flips =  randomFlips(len( words ), 0.8)  # allow 20% of rotation

    for i in range(len(sizes)):
        normalTokens.append( Token( words[i], sizes[i], 0 if flips[i] == 0 else 90 ) )

    return normalTokens



def drawWord(token):
    """
      gets an instance of Token class and draws the word it represents
      returns an image of the given word in the given font size
      the image is NOT cropped
    """

    font = ImageFont.truetype(FONT_NAME, token.fontSize)
    w, h = font.getsize(token.word)

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    draw.text((0, 0), token.word, font = font)

    #if token.drawAngle != 0:
    #    im = im.rotate( token.drawAngle,  expand=1)

    return im


def drawOnCanvas( normalTokens, canvas_size ):
    """
       given a list of tokens and a canvas size, we put the token images onto the canvas
       the places of each token on this canvas has already been determined during placeWords() call.

       Notice, that it is not required that the @place of each @token is inside the canvas;
       if necessary we may enlarge the canvas size to embrace these missing images
    """

    c_W,c_H = canvas_size        # the suggested canvas size, might change here

    # there might be some positions of words which fell out of the canvas
    # we first need to go through these exceptions (if any) and expand the canvas and (or) shift the coordinate's origin.

    X_min, Y_min = 0, 0

    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        if X_min > token.place[0]:
            X_min = token.place[0]

        if Y_min > token.place[1]:
            Y_min = token.place[1]


    x_shift, y_shift = 0, 0
    if X_min < 0:
        x_shift = -X_min
    if Y_min < 0:
        y_shift = -Y_min

    X_max , Y_max = 0, 0
    for i, token in enumerate(normalTokens):
        if token.place == None:
            continue

        token.place = ( token.place[0] + x_shift, token.place[1] + y_shift )
        if X_max < token.place[0] + token.imgSize[0]:
            X_max = token.place[0] + token.imgSize[0]
        if Y_max < token.place[1] + token.imgSize[1]:
            Y_max = token.place[1] + token.imgSize[1]

    c_W = max(c_W, X_max)
    c_H = max(c_H, Y_max)

    im_canvas = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = None )
    im_canvas_white = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = (255,255,255,255) )

    dd = ImageDraw.Draw(im_canvas)
    dd_white = ImageDraw.Draw(im_canvas_white)


    # add color to each word to be placed on canvas
    CH.colorTokens(normalTokens)

    for i, token in enumerate(normalTokens):
        if token.place == None:
            print('the word <' + token.word + '> was skipped' )
            continue

        font1 = ImageFont.truetype(FONT_NAME, token.fontSize)
        c = token.color

        dd.text( token.place, token.word, fill = c,  font = font1 )
        dd_white.text( token.place, token.word, fill = c,  font = font1 )


    margin_size = 10 # the border margin size
    box = im_canvas.getbbox()


    im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
    im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1


def createQuadTrees(normalTokens):
    """
        given a list of tokens we fill their quadTree attributes and cropped image size
    """

    for i, token in enumerate(normalTokens):
        im_tmp = drawWord(token)
        T = BBox.getQuadTree( im_tmp , QUADTREE_MINSIZE, QUADTREE_MINSIZE )
        T.compress()
        im_tmp = im_tmp.crop(im_tmp.getbbox())

        token.quadTree = T
        token.imgSize = im_tmp.size




def placeWords(normalTokens):
    """
      gets a list of tokens and their frequencies
      executes the placing strategy and
      returns canvas size, locations of upper-left corner of words and words' sizes
    """

    # 1. we first create the QuadTrees for all words and determine a size for the canvas

    word_img_path = [] # shows the path passed through the spiral before hitting a free space

    print('Number of tokens equals', len(normalTokens), '\n')

    T_start = timeit.default_timer()

    # create the quadTrees and collect sizes (width, height) of the cropped images of the words
    createQuadTrees(normalTokens)

    T_stop = timeit.default_timer()
    print('(i)  QuadTrees have been made for all words in', T_stop - T_start, 'seconds.','\n')

    #2. We now find places for the words on our canvas

    #c_W, c_H = 4000, 4000
    #c_W, c_H = 2000, 1000
    c_W, c_H = 3000, 1500
    #c_W, c_H = 1000, 1000


    print('(ii) Now trying to place the words.\n')
    sys.stdout.flush()

    T_start = timeit.default_timer()

    #3a. we start with the 1st word


    ups_and_downs = [ random.randint(0,20)%2  for i in range( len(normalTokens) )]
    #ups_and_downs = [ random.randint(0,51)%3  for i in range( len(normalTokens) )]

    for i, token in enumerate(normalTokens):
        print( token.word , end = ' ' )
        sys.stdout.flush()     # force the output to display what is in the buffer

        a = 0.2                # the parameter of the spiral

        if ups_and_downs[i] == 1:
            # add some randomness to the placing strategy
            a = -a


        # determine a starting position on the canvas of this token, near half of the width of canvas
        w, h =   random.randint( int(0.3*c_W), int(0.7*c_W) ) ,  (c_H >> 1) - (token.imgSize[1] >> 1)
        if w < 0 or w >= c_W:
            w = c_W >> 1
        if h < 0 or h >= c_H:
            h = c_H >> 1


        if ups_and_downs[i] == 0:
            A = SP.Archimedian(a).generator
        else:
            A = SP.Rectangular(2, ups_and_downs[i]).generator

        dx0, dy0 = 0, 0
        place1 = (w, h)

        word_img_path.append( (w,h) )

        last_hit_index = 0 # we cache the index of last hit

        iter_ = 0

        start_countdown = False
        max_iter = 0

        for dx, dy in A:
            w, h = place1[0] + dx, place1[1] + dy

            if start_countdown == True:
                max_iter -= 1
                if max_iter == 0:
                    break
            else:
                iter_ += 1

            if ( w < 0 or w >= c_W or h < 0 or h > c_H ):
                #  the shape has fallen outside the canvas
                if start_countdown == False:
                    start_countdown = True
                    max_iter  = 1 + 10*iter_


            place1 = ( w, h )
            collision = False

            if last_hit_index < i:
                j = last_hit_index
                if normalTokens[j].place != None:
                    collision = BBox.collisionTest( token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY)

            if collision == False:
                # NO collision with the cached index
                for j in range( i ): # check for collisions with the rest of the tokens
                    if ((j != last_hit_index) and (normalTokens[j].place != None)):
                        if BBox.collisionTest(token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY) == True:
                            collision = True
                            last_hit_index = j

                            break # no need to check with the rest of the tokens, try a new position now

            if collision == False:
                if BBox.insideCanvas( token.quadTree , place1, (c_W, c_H) ) == True:
                    # at this point we have found a place inside the canvas where the current token has NO collision
                    # with the already placed tokens; The search has been completed.
                    token.place = place1
                    break   # breaks the spiral movement
                else:
                    if token.place == None:
                        # even though this place is outside the canvas, it is collision free and we
                        # store it in any case to ensure that the token will be placed
                        token.place = place1




    T_stop = timeit.default_timer()

    print('\n Words have been placed in ' + str( T_stop - T_start ) + ' seconds.\n')


    return c_W, c_H




def createWordle_fromFile( fName ):
    # the master function, creates the wordle from a given text file

    tokens = FR.tokenize_file_IntoWords(fName)
    tokens, freq = FR.tokenGroup(tokens)

    print('\n')

    for i in range(  min(10, len(tokens) ) ):
        s = freq[i]
        print( str(s) +  (7-len(str(s)))*' ' + ':  ' + tokens[i]  )


    normalTokens =  normalizeWordSize(tokens, freq, TOKENS_TO_USE, FONT_SIZE_MAX, FONT_SIZE_MIN)
    canvas_W, canvas_H = placeWords(normalTokens)

    wordle = drawOnCanvas(normalTokens, (canvas_W, canvas_H ) )

    wordle.save( fName[0:-4] + '_wordle.png')

    print( 'the wordle image was sucessfully saved on the disc as <' + fName[0:-4]  + '_wordle.png >' )



if __name__ == "__main__":
    # waits for .txt fileName for processing
    createWordle_fromFile( sys.argv[1])
