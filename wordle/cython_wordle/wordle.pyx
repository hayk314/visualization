# Designed and implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

from __future__ import print_function  # to support end = '' parameter of the print

from PIL import Image, ImageColor, ImageFont, ImageDraw

import sys
import random

import timeit   # for calculating running time (TESTING purposes only)


import spirals as SP
import BBox
import Trees
from Trees import Node, Tree

# constants:
STAY_AWAY = 2             # force any two words to stay at least this number of pixels away from each other
QUADTREE_MINSIZE = 5      # minimal height-width of the box in quadTree partition
FONT_NAME = "arial.ttf"   # the font (true type) used to draw the word shapes


class Token:
    """
        encapsulates the main information on a token into a single class
        Token here represents a word to be placed on canvas for the final wordle Image

        most of the attributes are filled with functions during processing of the tokens
    """

    def __init__(self, word, fontSize = 10, drawAngle = 0):
        self.word = word
        self.fontSize = fontSize      # an integer
        self.drawAngle = drawAngle    # an integer representing the rotation angle of the image; 0 - for NO rotation
        self.imgSize = None           # integers (width, height) size of the image of this word with the given fontSize
        self.quadTree = None          # the quadTree of the image of this word with the above characteristics
        self.place = None             # tuple, the coordinate of the upper-left corner of the token on the final canvas
        self.color = None             # the fill color on canvas (R, G, B) triple




cdef drawWord(token):
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

    # TODO the rotation is not being used currently
    # if token.drawAngle != 0:
    #    im = im.rotate( token.drawAngle,  expand = 1)

    return im


cdef createQuadTrees(normalTokens):
    """
        given a list of tokens we fill their quadTree attributes and image size
    """

    for i, token in enumerate(normalTokens):
        im_tmp = drawWord(token)
        T = BBox.getQuadTree( im_tmp , QUADTREE_MINSIZE, QUADTREE_MINSIZE )
        T.compress()
        im_tmp = im_tmp.crop(im_tmp.getbbox())

        token.quadTree = T
        token.imgSize = im_tmp.size


cpdef placeWords(normalTokens):
    """
      gets a list of tokens and their frequencies
      executes the placing strategy and
      returns canvas size, locations of upper-left corner of words and words' sizes
    """

    # 1. we first create the QuadTrees for all words and determine a size for the canvas

    print('Number of tokens equals', len(normalTokens), '\n')

    T_start = timeit.default_timer()

    # create the quadTrees and collect sizes (width, height) of the word shapes
    createQuadTrees(normalTokens)

    T_stop = timeit.default_timer()
    print('(i)  QuadTrees have been made for all words in', T_stop - T_start, 'seconds.','\n')

    # 2. We now find places for the words on our canvas

    cdef int c_W = 3000
    cdef int c_H = 1500

    cdef int dx0 = 0
    cdef int dy0 = 0
    cdef int w = 0
    cdef int h = 0
    cdef int dx = 0
    cdef int dy = 0

    cdef int last_hit_index = 0 # we cache the index of last hit

    print('(ii) Now trying to place the words.\n')
    sys.stdout.flush()

    T_start = timeit.default_timer()

    # 3a. we start with the 1st word


    ups_and_downs = [ random.randint(0,20)%2  for i in range( len(normalTokens) )]


    for i, token in enumerate(normalTokens):
        print( token.word, end = ' ' )
        sys.stdout.flush()     # force the output to display what is in the buffer

        a = 0.2                # the parameter of the spiral

        if ups_and_downs[i] == 1:
            # add some randomness to the placing strategy
            a = -a


        # determine a starting position on the canvas of this token, near half of the width of canvas
        w = random.randint( int(0.3*c_W), int(0.7*c_W) )
        h = (c_H >> 1) - (token.imgSize[1] >> 1)

        if w < 0 or w >= c_W:
            w = c_W >> 1
        if h < 0 or h >= c_H:
            h = c_H >> 1


        if ups_and_downs[i] == 0:
            A = SP.Archimedian()
            A.start(a)
        else:
            A = SP.Rectangular()
            A.start(2)

        dx0, dy0 = 0, 0
        place1 = (w, h)

        last_hit_index = 0 # we cache the index of last hit

        iter_ = 0

        start_countdown = False
        max_iter = 0

        while True:
            w = place1[0] + A.u
            h = place1[1] + A.v
            A.getNext()


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
                if BBox.insideCanvas( token.quadTree , place1[0], place1[1], c_W, c_H ) == True:
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

    print('')
    print('\nWords have been placed in ' + str( T_stop - T_start ) + ' seconds.\n')


    return c_W, c_H
