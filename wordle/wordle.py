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
tokens_to_use = 250       # number of different tokens to use in the wordle
stay_away = 1             # force any two words to stay at least this number of pixels away from each other
font_size_min = 20        # the smallest font of a word
font_size_max = 300       # the largest font of a word
desired_HW_Ratio = 0.618  # height/widht ratio of the canvas
quadTree_minSize = 5      # minimal height-width of the box in quadTree partition


def proposeCanvasSize(quadTrees):
    # pased on the list of quadtrees we propose a canvase size, width and height
    area = 0
    boxArea = 0

    for t in quadTrees:
        area += t.areaCovered()               # this is the actual area covered by the image
        boxArea += Trees.rectArea(t.root)     # this is the area covered by the images's bounding box



def normalizeWordSize(tokens, freq, N_of_tokens_to_use, max_size, min_size):
    """
     (linearly) scale the font sizes of tokens to the range [min_size, max_size]
     and trim those tokens with size < min_size
    """

    words = tokens[:N_of_tokens_to_use]
    sizes = freq[:N_of_tokens_to_use]

    # sizes = [int(max_size*x/max(sizes)) for x in sizes]
    # scale the range of sizes to the given range [min_size, max_size]
    a, b = min(sizes), max(sizes)
    sizes = [  int(((max_size - min_size )/(b - a))*( x - a ) + min_size )  for x in sizes ]

    i = 0
    while i < len(sizes):
        if sizes[i] < min_size:
            del sizes[i]
            del words[i]
        else:
            i += 1



    return words, sizes



def drawWord(word, fsize):
    """
      returns an image of the given word in the given font size
      the image is NOT cropped
    """

    font = ImageFont.truetype("arial.ttf", fsize)
    w, h = font.getsize(word)

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    draw.text((0, 0), word, font = font)

    return im


def drawOnCanvas(words, sizes, placeInfo ):

    (c_W,c_H) = placeInfo[0]     # the suggested canvas size, might change here
    place = placeInfo[1]         # list of tuples, each for each word, showing the coordinate of the upper left corner
    word_img_size = placeInfo[2] # list of tuples, for each word, showing the size of the word's image

    word_img_path = placeInfo[3]

    assert(len(place) == len(word_img_size))

    # there might be some positions of words which fell out of the canvas
    # we first need to go through these exceptions, and expand the canvas and (or) shift the coordinate's origin.

    X_min, Y_min = 0, 0

    for i in range(len(place)):

        if place[i] == None:
            continue

        if X_min > place[i][0]:
            X_min = place[i][0]

        if Y_min > place[i][1]:
            Y_min = place[i][1]


    x_shift, y_shift = 0, 0
    if X_min < 0:
        x_shift = -X_min
    if Y_min < 0:
        y_shift = -Y_min

    X_max , Y_max = 0, 0
    for i in range( len(place) ):
        if place[i] == None:
            continue

        place[i] = ( place[i][0] + x_shift, place[i][1] + y_shift )
        if X_max < place[i][0] + word_img_size[i][0]:
            X_max = place[i][0] + word_img_size[i][0]
        if Y_max < place[i][1] + word_img_size[i][1]:
            Y_max = place[i][1] + word_img_size[i][1]

        word_img_path[i] = ( word_img_path[i][0] + x_shift, word_img_path[i][1] )


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

    max_size = max(sizes)

    for i in range( len(place) ):
        if place[i] is None:
            print('the word <' + words[i] + '> was skipped' )
        else:
            font1 = ImageFont.truetype("arial.ttf", sizes[i])

            if sizes[i] >= 0.7*max_size:
                c = word_colors[-1]
            elif ((sizes[i] >= 0.5*max_size)and(sizes[i]<0.7*max_size) ):
                c = word_colors[-2]
            elif ((sizes[i] >= 0.35*max_size)and(sizes[i]<0.5*max_size) ):
                c = word_colors[-3]
            elif ((sizes[i] >= 0.15*max_size)and(sizes[i]<0.35*max_size) ):
                c = word_colors[-4]
            else:
                c = word_colors[-5]


            dd.text( place[i], words[i], fill = c,  font = font1 )
            dd_white.text( place[i], words[i], fill = c,  font = font1 )


    margin_size = 10

    box = im_canvas.getbbox()


    im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
    im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1


def createQuadTrees(words, sizes):
    """
        given a list of words and their corresponding font-szies, we create QuadTrees for each word
        and return 2 lists, one for the quadtrees and another for sizes of the cropped word-images
    """
    tree_list, size_list = [], []

    for i in range( len(words) ):
        im_tmp = drawWord(words[i], sizes[i] )
        T = BBox.getQuadTree( im_tmp , 7, 7 )
        T.compress()
        tree_list.append( T )

        im_tmp = im_tmp.crop(im_tmp.getbbox())
        size_list.append(im_tmp.size)

    return tree_list, size_list



def placeWords(words, sizes):
    """
      gets a list of tokens and their frequencies
      executes the placing strategy and
      returns canvas size, locations of upper-left corner of words and words' sizes
    """

    # 1. we first create the QuadTrees for all words and determine a size for the canvas

    word_img_path = [] # shows the path passed through the spiral before hitting a free space

    print('Number of words equals', len(words), '\n')

    T_start = timeit.default_timer()

    # create the quadTrees and collect sizes (width, height) of the cropped images of the words
    word_Trees, word_img_size = createQuadTrees(words, sizes)

    T_stop = timeit.default_timer()
    print('(i)  QuadTrees have been made for all words in', T_stop - T_start, 'seconds.','\n')

    #2. We now find places for the words on our canvas

    c_W, c_H = 2000, 1200
    #c_W, c_H = 3000, 1500


    print('(ii) Now trying to place the words.\n')
    sys.stdout.flush()

    T_start = timeit.default_timer()

    #3a. we start with the 1st word


    places = [ ]  #returned value; list of tuples representing places of words: if no suggested place, we put NONE
    ups_and_downs = [ random.randint(0,20)%2  for i in range( len(words) )]

    strLog = '' # the log file

    for i, word in enumerate(words):

        print( word , end = ' ' )
        sys.stdout.flush()  # force the output to display what is in the buffer

        strLog_word = '<' + word + '>\n'

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
            if sizes[i] < 0.3*max( sizes ):
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )
            else:
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )


        strLog_word += '   Starting position: (' + str(w) + ',' +str(h) + ')\n'

        if ups_and_downs[i] == 1:
            A = SP.Archimedian(a).generator
        else:
            A = SP.Rectangular(2, ups_and_downs[i]).generator

        dx0, dy0 = 0, 0

        place1 = (w,h)

        word_img_path.append( (w,h) )

        last_hit_index = 0 #we cache the index of last hit

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
                if places[j] is not None:
                    if BBox.collisionTest(word_Trees[i], word_Trees[j], place1, places[j], stay_away) == True:
                        collision = True

            if collision == False:
                for j in range( i ): #check for collisions with the rest
                    if ((j != last_hit_index) and (places[j] is not None)):
                        if BBox.collisionTest(word_Trees[i], word_Trees[j], place1, places[j], stay_away) == True:
                            collision = True
                            last_hit_index = j
                            break

            if collision == False:
                if BBox.insideCanvas( word_Trees[i] , place1, (c_W, c_H) ) == True:
                    places.append( place1 )
                    place_found = True
                    strLog_word += '    Place was found\n'
                    break # breaks the move in the Archimedian spiral
                else:
                    no_collision_place.append(  place1  )




        if place_found == False:
            print('no place was found')

            strLog_word += '    Number of collision_free_outside canvas places =' + str(len(no_collision_place)) +'\n'

            if not no_collision_place:
                places.append(None)
            else:
                if  i == 0 : # the first word
                    places.append( no_collision_place[0]  )
                else:
                    # print('BUT there is some outside the canvas')

                    #k1, k2 = int(0.5*c_W), int(0.5*c_H) #the centre of the canvas
                    k1, k2 =  int(0.5*(places[0][0] + word_img_size[0][0])), int(0.5*(places[0][1] + word_img_size[0][1]))

                    place1 = no_collision_place[0]
                    c_x, c_y = int(0.5*(place1[0] + word_img_size[i][0])),  int(0.5*(place1[1] + word_img_size[i][1]))
                    ds = (k1 - c_x)**2 + (k2 - c_y)**2
                    d_index = 0
                    for p in range(1, len(no_collision_place)):
                        place1 = no_collision_place[p]
                        c_x, c_y = int(0.5*(place1[0] + word_img_size[i][0])),  int(0.5*(place1[1] + word_img_size[i][1]))
                        ds_1 = (k1 - c_x)**2 + (k2 - c_y)**2
                        if ds_1<ds:
                            ds, d_index = ds_1 , p

                    places.append( no_collision_place[d_index] )
                    #NOTE!!! - - -  - - - TODO -  - - - - - -- -
                    #if the no collision place has negative (x or y), we need
                    #to to replace the origin of the canvas to accommodate those words



        strLog += strLog_word + '\n' + 'New size of the canvas = (' + str(c_W) +',' +  str(c_H)  +  ')\n\n'

    T_stop = timeit.default_timer()

    print('\n Words have been placed in ' + str( T_stop - T_start ) + ' seconds.\n')

    #with open('LogFile.txt', 'w+') as f:
    #    f.write(strLog)

    return [ (c_W, c_H),  places , word_img_size, word_img_path ]




def createWordle_fromFile( fName ):
    # the master function, creates the wordle from a given text file

    tokens = FR.tokenize_file_IntoWords(fName)
    tokens, freq = FR.tokenGroup(tokens)

    print('\n')

    for i in range(  min(10, len(tokens) ) ):
        s = freq[i]
        print( str(s) +  (7-len(str(s)))*' ' + ':  ' + tokens[i]  )


    #N_of_words = 150
    tokens, freq =  normalizeWordSize(tokens, freq, tokens_to_use, font_size_max, font_size_min)
    finalPlaces = placeWords(tokens, freq)

    wordle = drawOnCanvas(tokens, freq, finalPlaces)

    wordle.save( fName[0:-4] + '_wordle.png')

    print( 'the wordle image was sucessfully saved on the disc as <' + fName[0:-4]  + '_wordle.png >' )



if __name__ == "__main__":
    # waits for .txt fileName for processing
    createWordle_fromFile( sys.argv[1])
