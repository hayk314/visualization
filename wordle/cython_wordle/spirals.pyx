# Author: Hayk Aleksanyan
# create and test Archimedian and rectangular spirals

from libc.math cimport sin, cos


cdef class Archimedian:
    # models the Archimedian spiral with the given parameter

    cdef public param
    cdef public double x
    cdef public double y
    cdef double step_size
    cdef public int u
    cdef public int v
    cdef public double r

    def start(self, param):
        self.param = param
        self.x = 0.0
        self.y = 0.0
        self.step_size = 0.5
        self.u = 0
        self.v = 0
        self.r = 0.0


    def get_next(self):
        """
         generator for the Archimedian spiral r = a*\phi (in polar coordinates)
         generated coordinates are in (x,y) plane
        """

        self.r += self.step_size
        self.x =  self.param*self.r*cos(self.r)
        self.y =  self.param*self.r*sin(self.r)

        if (( int(self.x - self.u) == 0 ) and ( int(self.y - self.v) == 0 ) ):
                # forcing a move
                self.get_next()
        else:
            self.u = int(self.x)
            self.v = int(self.y)



cdef class Rectangular:
    # Models a Rectangular spiral  with the given parameters

    cdef public int param
    cdef public int u
    cdef public int v
    cdef public int m
    cdef public int step
    cdef public int phase

    def start(self, param):
        self.param = param
        self.u = 0
        self.v = 0
        self.phase = 0
        self.step = 0
        self.m = param


    def get_next(self):
        """
           generator for rectangular spiral
           directions = [ (0,-1), (1,0), (0, 1), (-1, 0) ]

           if reverse = 1, then we make the normal way,
           otherwise, if reverse = -1, then we do mirror reflection in (x,y)
        """

        if self.phase == 0:
            if self.step < self.m:
                self.v -= 1

                self.step += 1
            else:
                self.step = 0
                self.phase = 1
                self.get_next()

        elif self.phase == 1:
            if self.step < self.m:
                self.u += 1

                self.step += 1
            else:
                self.step = 0
                self.phase = 2
                self.m += self.param

                self.get_next()

        elif self.phase == 2:
            if self.step < self.m:
                self.v += 1
                self.step += 1
            else:
                self.step = 0
                self.phase = 3
                self.get_next()

        elif self.phase == 3:
            if self.step < self.m:
                self.u -= 1
                self.step += 1
            else:
                self.step = 0
                self.phase = 0
                self.m += self.param

                self.get_next()
