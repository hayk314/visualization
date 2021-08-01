# Author: Hayk Aleksanyan
# testing wordle related utils
# anything in this module is for illustration/test purposes only

from PIL import Image, ImageColor, ImageFont, ImageDraw

import random   # used for random placement of the initial position of a word

import timeit   # for calculating running time (TESTING purposes only)

import numpy as np
import sys

import spirals as SP
import bbox


def colorBBoxesBorders(im, T, shift = (0, 0) ):
    """
        takes an image @im and a Tree @T corresponding to the bounding box hierarchy (quad-tree partition)
        colors only the borders of bounding rectangles
    """

    w = 1  # the (symmetric) width of the border of rectangles to be colored

    im_1 = im.copy()
    (W, H) = im_1.size

    Boxes = T.get_node_value_list()

    for i in range( len(Boxes) ):
        z = Boxes[i]

        for u in range(z[0] + shift[0] , z[2] + shift[0] ):
            for v in range( z[1] + shift[1] - w, z[1] + shift[1] + w + 1 ):
                if ( (v >= 0 ) and (v < H) ):
                    im_1.putpixel( (u, v), (255, 0, 0, 0) )

            for v in range( z[3] + shift[1] - w, z[3] + shift[1] + w + 1 ):
                if ( (v >= 0) and ( v < H ) ):
                    im_1.putpixel( (u, v), (255, 0, 0, 0) )


        for u in range( z[1] + shift[1], z[3] + shift[1] ):
            for v in range( z[0] + shift[0] - w, z[0] + shift[0] + w + 1 ):
                if ( ( v >= 0 ) and ( v < W ) ):
                    im_1.putpixel( (v, u), (255, 0, 0, 0) )

            for v in range( z[2] + shift[0] - w, z[2] + shift[0] + w + 1 ):
                if ( ( v >= 0 ) and ( v < W ) ):
                    im_1.putpixel( (v, u), (255, 0, 0, 0) )


    return im_1


def colorBoxes( im, Boxes, shift = (0,0) ):
    """
       gets an image @im and a list of rectangles (in upper-left - bottom-right coordinates) @Boxes
       @shift parameter can be used to shift the rectanlges in the coordinate system.

       This function colors bounding boxes @Boxes of the image @im in red and returns this colored image
    """
    im_1 = im.copy()

    for i in range( len(Boxes) ):
        z = Boxes[i].value
        for u in range(z[0] + shift[0] , z[2] + shift[0] ):
            for v in range(z[1] + shift[1] , z[3] + shift[1] ):
                im_1.putpixel( (u, v), (255, 0, 0, 0) )

    return im_1


def drawWord(word, fsize):
    # returns the cropped image of the @word with Font.size = @fsize

    font = ImageFont.truetype("fonts/arial.ttf", fsize)
    w, h = font.getsize( word )

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    draw.text( (0, 0), word, font = font )

    box_0 = im.getbbox() # the initial bounding box
    im = im.crop(box_0)

    return im


def testQuadTrees(testWord = "test", fontSize = 200):
    # create quadtree of the given test-word  with a given font size, and apply tree compression (pruning)
    # save the images of colored bounding boxes

    T_start = timeit.default_timer()

    im = drawWord(testWord, fontSize)
    T_stop = timeit.default_timer()
    print('\n1. Word image ready in ', T_stop - T_start, 'seconds.')

    T_start = timeit.default_timer()

    T = bbox.construct_quadtree(im, 7, 7)

    T_stop = timeit.default_timer()
    print('2. Quad tree ready in ', T_stop - T_start, 'seconds.')

    T_start = timeit.default_timer()

    im_colored_boxes = colorBBoxesBorders(im, T)

    T_stop = timeit.default_timer()
    print('3. Coloring of the uncompressed tree took ', T_stop - T_start, 'seconds.')


    T_start = timeit.default_timer()
    T.compress()
    T_stop = timeit.default_timer()
    print('4. Tree compression ready in ', T_stop - T_start, 'seconds.')

    T_start = timeit.default_timer()

    im_color_boxes_pruned = colorBBoxesBorders(im, T)

    T_stop = timeit.default_timer()
    print('5. Coloring of the compressed tree took ', T_stop - T_start, 'seconds.','\n')

    # convert RGBA to RGB allowing the files to be saved as png
    im_colored_boxes_back = Image.new('RGB', im_colored_boxes.size, (0,0,0))
    im_colored_boxes_back.paste( im_colored_boxes)

    im_color_boxes_pruned_back = Image.new('RGB', im_color_boxes_pruned.size, (0,0,0))
    im_color_boxes_pruned_back.paste( im_color_boxes_pruned )

    im_colored_boxes_back.save(testWord + '_BBox.png')
    im_color_boxes_pruned_back.save(testWord + '_pruned_BBox.png')

    print('The output saved on ', testWord + '_BBox.png', ' and ', testWord + '_pruned_BBox.png', '\n')



def testSpirals(**spiralArgs):
    # testing the spirals

    if not 'type' in spiralArgs:
        print('the spiral type is not specified, terminating.')
        return

    t = spiralArgs['type']
    if t == 1:
        if not 'param' in spiralArgs:
            a =  0.2
        else:
            a = spiralArgs['param']
        A = SP.Archimedian(a)
    elif t == 2:
        if not 'param' in spiralArgs:
            a = 2
        else:
            a = spiralArgs['param']
        A = SP.Rectangular(a)
    elif t == 3:
        if not 'param' in spiralArgs:
            a = 2
        else:
            a = spiralArgs['param']
        A = SP.RandomWalk(a)
    else:
        print('unknown spiral type, terminating')
        return

    if 'iter' in spiralArgs:
        iterN = spiralArgs['iter']
    else:
        iterN = 1000
    if 'dump' in spiralArgs:
        dump = spiralArgs['dump']
        if 'dumpFreq' in spiralArgs:
            dumpFreq = spiralArgs['dumpFreq']
        else:
            dumpFreq = 0
    else:
        dump, dumpFreq = False, 0

    im = A.draw(1000, 1000, iterN, dump, dumpFreq)
    fName = A.name + '_iter=' + str(iterN) + '.png'
    im.save(fName)
    print('\nThe spiral image saved on ', fName)


def testingDirective():
    # start a process of testing, promping the user until they wish to terminate

    print('\nStarting testing process of QuadTrees and Sprials.')
    print('To stop please type the text inside the quotes: "STOP"\n')

    while True:

        userInput = input("For QuadTrees type 1, for Spirals type 2, anything else will terminate the process.\n")
        if userInput  != '1' and userInput != '2':
            print('exiting...')
            return

        if userInput == '1':
            inputStr = input('please type the word to build the Quad Tree on\n')
            if len(inputStr) == 0:
                print('empty string, nothing to do\n')
                continue
            elif len(inputStr) > 100:
                print('please restrict the input to maximum 100 characters\n')
                continue

            inputFontSize = input('please type the font size, an integer between 1 and 1000\n')
            if not inputFontSize.isdigit():
                print('the input is not an integer, nothing to do')
                continue

            inputFontSize = int(inputFontSize)
            if not 0 < inputFontSize <= 1000:
                print('please keep the font size between 1 and 1000')
                continue

            print('\n')
            testQuadTrees(testWord = inputStr , fontSize = inputFontSize)
            print('\n')

        if userInput == '2':
            inputType = input('please type the 1 for Archimedian spiral, 2 for Rectangular spiral, 3 for Random Walks\n')

            if not inputType in {'1', '2', '3'}:
                print('invalid type, nothing to do\n')
                continue

            inputType = int(inputType)

            inputParam = input('please type the parameter of the spiral\n')
            try:
                inputParam = float(inputParam)
            except:
                print('the parameter must be numeric')
                continue

            if inputParam <= 0:
                print('the parameter must be positive\n')
                continue
            if inputType != 1:
                inputParam = int(inputParam)
                if inputParam == 0:
                    inputParam = 1

            inputIterN = input('please type the iteration count, a positive integer\n')
            if not inputIterN.isdigit() or int(inputIterN) <= 0:
                print('the iteration count must be positive\n')
                continue

            print('\n')
            testSpirals(type = inputType, param = inputParam, iter = inputIterN  )
            print('\n')



if __name__ == "__main__":
    # simply follow the prompt of the program
    testingDirective()
