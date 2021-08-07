# Author: Hayk Aleksanyan
# support for various types of 2d spirals

import math
import numpy as np
import os
from PIL import Image


class SpiralBase:
    """
       the base class of a 2d spiral
    """

    def __init__(self, generator):
        """ the generator of the spiral, will be initialized through a derived class for specific spiral types """
        self.generator = generator

    @property
    def name(self):
        return type(self).__name__

    @staticmethod
    def get_alias():
        return ""

    def draw(self, width, height, n_of_iter, snapshot_freq=-1):
        """
         draw the spiral based on the generator @gen on a 2d canvas of the given @width and @height
         use next @N_of_iter items of the generator

         if @snapshot_freq > 0 then we save the result of iteration each @snapshot_freq intervals

         NOTE!! <draw> method will alter the state of the generator, this is only for testing purposes
        """

        (c_x, c_y) = (int(0.5 * width), int(0.5 * height))
        im_canvas = np.zeros((width, height), dtype='uint8')

        n, t = 0, 0  # counting iterations

        if snapshot_freq > 0:
            output_folder = os.path.join("tmp", self.name)
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

        for dx, dy in self.generator:
            u, v = c_x + dx, c_y + dy
            if (u < 0) or (v < 0) or (u > width - 1) or (v > height - 1):
                # out of borders
                print('[{}] Fell outside the border of the canvas on coordinate [{}]'.format(self.name, (u, v)),
                      flush=True)
                break

            n += 1
            im_canvas[u, v] = 255
            if n % 10 == 0:
                print(n, end=' ', flush=True)
            if n == n_of_iter:
                break

            if snapshot_freq > 0 and n % snapshot_freq == 0:
                t += 1
                im_1 = Image.fromarray(im_canvas)
                im_1.save(os.path.join(output_folder, "test_" + str(t) + ".png"))

        return Image.fromarray(im_canvas)

    def output_visited_sites(self, n_of_iter):
        """
          outputs the next @N_of_iter items of the spiral's generator
          NOTE!! <print> will alter the state of the generator, this is only for testing purposes
        """

        n = 0
        for dx, dy in self.generator:
            print("x = {}, y = {}".format(dx, dy))
            n += 1
            if n == n_of_iter:
                break


class Archimedian(SpiralBase):
    """
        Models the Archimedian spiral with the given parameter
    """

    def __init__(self, param):
        super().__init__(self.spiral(param))

    @staticmethod
    def get_alias():
        return "arch"

    def spiral(self, a):
        """
         generator for the Archimedian spiral r = a*\phi (in polar coordinates)
         generated coordinates are in (x,y) plane
        """

        r = 0
        step_size = 0.5

        u, v = 0, 0

        yield 0, 0

        while True:
            r += step_size
            x, y = a * r * math.cos(r), a * r * math.sin(r)

            if (int(x - u) == 0) and (int(y - v) == 0):  # forcing a move
                continue

            u, v = int(x), int(y)
            yield u, v


class Rectangular(SpiralBase):
    """ Models a Rectangular spiral  with the given parameters """

    def __init__(self, param, reverse=1):
        param = int(param)
        super().__init__(self.spiral(param, reverse))

    @staticmethod
    def get_alias():
        return "rect"

    def spiral(self, a, reverse):
        """
         generator for rectangular spiral
         directions = [(0,-1), (1,0), (0, 1), (-1, 0)]

         if reverse, then spiral the normal way, otherwise, do mirror reflection in (x,y)
        """

        x, y = 0, 0
        yield x, y

        m = a

        while True:
            i = 0
            while i < m:
                y -= 1
                i += 1

                if reverse:
                    yield x, y
                else:
                    yield -x, -y

            i = 0
            while i < m:
                x += 1
                i += 1

                if reverse:
                    yield x, y
                else:
                    yield -x, -y

            i = 0
            m = m + a

            while i < m:
                y += 1
                i += 1

                if reverse:
                    yield x, y
                else:
                    yield -x, -y

            i = 0
            while i < m:
                x -= 1
                i += 1

                if reverse:
                    yield x, y
                else:
                    yield -x, -y

            m = m + a


class RandomWalk(SpiralBase):
    """
        Models symmetric random walk on integer lattice starting at the origin having the given step size
    """

    def __init__(self, param):
        param = int(param)
        super().__init__(self.spiral(param))

        self.random_directions = np.random

        self._buffer_size = 1024
        self._directions = None
        self._pointer = 0

        self.update_random_direction_buffer()

    @staticmethod
    def get_alias():
        return "randomwalk"

    def update_random_direction_buffer(self):
        self._directions = np.random.randint(0, 4, self._buffer_size)
        self._pointer = 0

    def get_random_direction(self):
        d = self._directions[self._pointer]

        self._pointer += 1
        if self._pointer == self._buffer_size:
            self.update_random_direction_buffer()

        return d

    def spiral(self, a):
        """
         generator for random walk with step size = a
         the walk start from the origin (0,0)
         move directions = [(0,-1), (1,0), (0, 1), (-1, 0)]
        """

        x, y = 0, 0
        yield x, y

        while True:
            p = self.get_random_direction()

            if p == 0:
                y -= a
            elif p == 1:
                x += a
            elif p == 2:
                y += a
            else:
                x -= a

            yield x, y
