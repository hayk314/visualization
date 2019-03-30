# Author: Hayk Aleksanyan
# create and test Archimedian and rectangular spirals
import math
import numpy as np
from PIL import Image


class SpiralBase:
    # the base class of spiral, anything in common for all spirals goes here

    def __init__(self, generator = None ):
        # the generator of the spiral, this is initialized through a derived class for specific spiral types
        self.generator = generator


    def draw(self, width, height, N_of_iter, dumpSnapshots = False):
        """
         draw the spiral based on the generator @gen on a 2d canvas of the given @width and @height
         use next @N_of_iter items of the generator

         if @dumpSnapshots == True, then we save the result of iteration each 5 itervals

         NOTE!! <draw> method will alter the state of the generator, this is only for testing purposes
        """
        N = 0

        (c_x, c_y) = (  int( 0.5*width), int( 0.5*height ) )
        im_canvas = np.zeros(( width, height ), dtype = 'uint8' )
        #im_canvas = Image.new('RGBA', (width, height), color = None)

        t = 0

        M = self.generator
        for dx, dy in M:
            u, v = c_x + dx , c_y + dy
            if ( (u < 0 ) or ( v < 0 ) or ( u > width - 1 ) or ( v > height - 1 ) ):
                # out of borders
                continue
            #im_canvas.putpixel( (u,v), (255,0,0,0) )

            N += 1
            #im_canvas[u,v] = int( 255*(max(0.5, float(N/N_of_iter))) )
            im_canvas[u,v] = 255
            print(N, end = ' ', flush = True)
            if N == N_of_iter:
                break

            if dumpSnapshots == True and N % 5 == 0:
                t += 1
                im_1 = Image.fromarray(im_canvas)
                im_1.save("test_" + str(t) + ".png")


        return Image.fromarray(im_canvas)

    def print(self, N_of_iter):
        """
          outputs the next @N_of_iter items of the spiral's generator
          NOTE!! <print> will alter the state of the generator, this is only for testing purposes
        """
        M = self.generator

        n = 0
        for dx, dy in M:
            print("x = {}, y = {}".format(dx, dy) )
            n += 1
            if n == N_of_iter:
                break





class Archimedian(SpiralBase):

    def __init__(self, param):
        self.param = param
        self.generator = self.Arch_spiral(self.param)

    def Arch_spiral(self, a):
        """
         generator for the Archimedian spiral r = a*\phi (in polar coordinates)
         generated coordinates are in (x,y) plane
        """
        r = 0
        step_size = 0.5

        u, v = 0, 0

        yield(0,0)

        while True:
            r += step_size
            x, y = a*r*math.cos(r), a*r*math.sin(r)

            if (( int(x - u) == 0 ) and ( int(y - v) == 0 ) ):
                continue
            else:
                u, v = int(x), int(y)
                yield ( u, v )

            #yield (int(x), int(y))


class Rectangular(SpiralBase):
    # rectangular spiral
    def __init__(self, param, reverse = 1):

        self.param = param
        self.reverse = reverse

        self.generator = self.Rect_spiral(self.param, self.reverse)

    def Rect_spiral(self, a, reverse = 1):
        """
         generator for rectangular spiral
         directions = [ (0,-1), (1,0), (0, 1), (-1, 0) ]

         if reverse = 1, then we make the normal way,
         otherwise, if reverse = -1, then we do mirror reflection in (x,y)
        """

        x, y = 0, 0
        yield (x,y)
        m = a
        i = 0

        while True:
            i = 0
            while ( i < m ):
                y -= 1
                i += 1

                if reverse == 1:
                    yield (x,y)
                else:
                    yield (-x, -y)

            i = 0
            while ( i < m ):
                x += 1
                i += 1

                if reverse == 1:
                    yield (x,y)
                else:
                    yield (-x, -y)

            i = 0
            m = m + a

            while (i < m):
                y += 1
                i += 1

                if reverse == 1:
                    yield (x,y)
                else:
                    yield (-x, -y)

            i = 0
            while (i<m):
                x -= 1
                i += 1

                if reverse == 1:
                    yield (x,y)
                else:
                    yield (-x, -y)

            m = m + a
