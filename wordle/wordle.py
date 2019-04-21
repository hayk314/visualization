# Implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

from PIL import Image
from PIL import ImageColor
from PIL import ImageFont
from PIL import ImageDraw

import math     # for sin, cos
import random   # used for random placement of the initial position of a word

import timeit   # for calculating running time (TESTING purposes only)

import numpy as np
import sys


import fileReader as FR
import spirals as SP
import BBox
import Trees
from Trees import Node
from Trees import Tree

# constants:
TOKENS_TO_USE = 200       # number of different tokens to use in the wordle
STAY_AWAY = 2             # force any two words to stay at least this number of pixels away from each other
FONT_SIZE_MIN = 20        # the smallest font of a word
FONT_SIZE_MAX = 300       # the largest font of a word
DESIRED_HW_RATIO = 0.618  # height/widht ratio of the canvas
QUADTREE_MINSIZE = 5      # minimal height-width of the box in quadTree partition



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


def proposeCanvasSize(quadTrees):
    # pased on the list of quadtrees we propose a canvase size, width and height
    area = 0
    boxArea = []

    for t in quadTrees:
        area += t.areaCovered()                            # this is the actual area covered by the image
        boxArea.append( Trees.rectArea(t.root.value) )     # this is the area covered by the images's bounding box

    ensure_space = 5    # force the sum of the total area to cover at least first @ensure_space tokens
    #print(boxArea)     # notice that quadTrees come sorted in DESC order, i.e. the trees of the bigger words come first

    total = area + sum ( boxArea[:ensure_space] )
    w = int ( math.sqrt(total/DESIRED_HW_RATIO) ) + 1
    h = int(DESIRED_HW_RATIO*w) + 1

    print('Ratio of the area covered by trees over the total area of bounding boxes of words',  area/sum(boxArea))
    return w, h


def normalizeWordSize(tokens, freq, N_of_tokens_to_use, max_size, min_size):
    """
     (linearly) scale the font sizes of tokens to the range [min_size, max_size]
     and trim those tokens with size < min_size
    """

    words = tokens[:N_of_tokens_to_use]
    sizes = freq[:N_of_tokens_to_use]

    normalTokens = [ ] # the list of Tokens to be returned

    # scale the range of sizes to the given range [min_size, max_size]
    a, b = min(sizes), max(sizes)
    sizes = [  int(((max_size - min_size )/(b - a))*( x - a ) + min_size )  for x in sizes ]

    for i in range(len(sizes)):
        normalTokens.append( Token( words[i], sizes[i] ) )

    return normalTokens



def drawWord(token):
    """
      gets an instance of Token class and draws the word it represents
      returns an image of the given word in the given font size
      the image is NOT cropped
    """

    font = ImageFont.truetype("arial.ttf", token.fontSize)
    w, h = font.getsize(token.word)

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    draw.text((0, 0), token.word, font = font)

    return im


def drawOnCanvas( normalTokens, canvas_size ):

    c_W,c_H = canvas_size        # the suggested canvas size, might change here

    # there might be some positions of words which fell out of the canvas
    # we first need to go through these exceptions, and expand the canvas and (or) shift the coordinate's origin.

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

    if c_W < X_max:
        c_W = X_max
    if c_H < Y_max:
        c_H = Y_max

    im_canvas = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = None )
    im_canvas_white = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = (255,255,255,255) )

    dd = ImageDraw.Draw(im_canvas)
    dd_white = ImageDraw.Draw(im_canvas_white)

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

    max_size = FONT_SIZE_MAX

    for i, token in enumerate(normalTokens):
        if token.place == None:
            print('the word <' + token.word + '> was skipped' )
            continue

        font1 = ImageFont.truetype("arial.ttf", token.fontSize)

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


        dd.text( token.place, token.word, fill = c,  font = font1 )
        dd_white.text( token.place, token.word, fill = c,  font = font1 )


    margin_size = 10

    box = im_canvas.getbbox()


    im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
    im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1


def createQuadTrees(normalTokens):
    """
        given a list of words and their corresponding font-szies, we create QuadTrees for each word
        and return 2 lists, one for the quadtrees and another for sizes of the cropped word-images
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
    #c_W, c_H = 2000, 1200
    c_W, c_H = 3000, 1500


    print('(ii) Now trying to place the words.\n')
    sys.stdout.flush()

    T_start = timeit.default_timer()

    #3a. we start with the 1st word


    ups_and_downs = [ random.randint(0,20)%2  for i in range( len(normalTokens) )]

    strLog = '' # the log file

    for i, token in enumerate(normalTokens):
        print( token.word , end = ' ' )
        sys.stdout.flush()  # force the output to display what is in the buffer

        strLog_word = '<' + token.word + '>\n'

        a = 0.1 #the parameter of the spiral
        place_found = False

        if ups_and_downs[i] == 1:
            a = -a

        no_collision_place = [] # in case we don't get a place inside canvas,
                                # we collect legal (i.e. collision-free) places for further use

        # get some starting position on the canvas, in a strip near half of the width of canvas

        w, h = 0, 0
        if i == 0:
            w, h =  np.random.randint( int(0.3*c_W), int(0.5*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )
        else:
            if token.fontSize < 0.3*FONT_SIZE_MAX:
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )
            else:
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )


        strLog_word += '   Starting position: (' + str(w) + ',' +str(h) + ')\n'

        if ups_and_downs[i] == 1:
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

            if ( (w<0)or(w>c_W)or(h<0)or(h>c_H) ):
                # fell outside the canvas area
                if start_countdown == False:
                    start_countdown = True
                    max_iter  = 1 + 10*iter_

                    strLog_word += '    Exited the canvas on step =' + str(iter_) + ' at (' + str(w) + ','  + str(h) +')\n'
                    strLog_word += '    Max_iter to complete =' + str(max_iter) +'\n'


            place1 = ( w, h )
            collision = False

            if last_hit_index < i:
                j = last_hit_index
                if normalTokens[j].place != None:
                    if BBox.collisionTest( token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY) == True:
                        collision = True

            if collision == False:
                for j in range( i ): # check for collisions with the rest
                    if ((j != last_hit_index) and (normalTokens[j].place != None)):
                        if BBox.collisionTest(token.quadTree, normalTokens[j].quadTree, place1, normalTokens[j].place, STAY_AWAY) == True:
                            collision = True
                            last_hit_index = j
                            break

            if collision == False:
                if BBox.insideCanvas( token.quadTree , place1, (c_W, c_H) ) == True:
                    token.place = place1
                    place_found = True
                    strLog_word += '    Place was found\n'
                    break # breaks the move in the Archimedian spiral





        strLog += strLog_word + '\n' + 'New size of the canvas = (' + str(c_W) +',' +  str(c_H)  +  ')\n\n'

    T_stop = timeit.default_timer()

    print('\n Words have been placed in ' + str( T_stop - T_start ) + ' seconds.\n')

    #with open('LogFile.txt', 'w+') as f:
    #    f.write(strLog)

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
