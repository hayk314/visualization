# Author: Hayk Aleksanyan
# create bounding hierarchical boxes for word shapes

from Trees import Node, Tree



def intersectionRect(r1, r2, shift1 = (0,0), shift2 = (0,0), extraSize = 3 ):
    """
     gets two 4-tuples of integers representing a rectangle in min,max coord-s
     optional params. @shifts can be used to move boxes on a larger canvas (2d plane)
                      @extraSize, forces the rectangles to stay away from each other by the given size (number of pixels)

     returns True if the rectangles intersect
    """

    if ((min(r1[0] - extraSize + shift1[0] , r1[2] + extraSize + shift1[0] ) > max( r2[0] - extraSize + shift2[0], r2[2] + extraSize + shift2[0] ) )
        or ( max(r1[0] - extraSize + shift1[0], r1[2] + extraSize + shift1[0] ) < min( r2[0] - extraSize + shift2[0], r2[2] + extraSize + shift2[0] ) ) ):
        return False

    if ((min(r1[1] - extraSize + shift1[1] , r1[3] + extraSize + shift1[1] ) > max( r2[1] - extraSize + shift2[1], r2[3] + extraSize + shift2[1]) )
        or ( max(r1[1] - extraSize + shift1[1], r1[3]  + extraSize + shift1[1] ) < min( r2[1] - extraSize + shift2[1], r2[3]+ extraSize + shift2[1] ) ) ):
        return False

    return True

cdef intersectionRect_C(int r10, int r11, int r12, int r13, int r20, int r21, int r22, int r23, int shift10 = 0, int shift11 = 0, int shift20 = 0, int shift21 = 0, int extraSize = 3):
    """
       the same function as intersectionRect, but with all variables having static types (c-style cython function)
       this function is the most used utility function when checking for collisions, and improving it even slightly
       has a visible effect on the overall performance
    """
    if ((min(r10 - extraSize + shift10 , r12 + extraSize + shift10 ) > max( r20 - extraSize + shift20, r22 + extraSize + shift20 ) )
        or ( max(r10 - extraSize + shift10, r12 + extraSize + shift10 ) < min( r20 - extraSize + shift20, r22 + extraSize + shift20 ) ) ):
        return False

    if ((min(r11 - extraSize + shift11 , r13 + extraSize + shift11 ) > max( r21 - extraSize + shift21, r23 + extraSize + shift21) )
        or ( max(r11 - extraSize + shift11, r13  + extraSize + shift11 ) < min( r21 - extraSize + shift21, r23 + extraSize + shift21 ) ) ):
        return False

    return True



def getQuadTree(im, minW, minH):
    """
      returns the quad-tree representation of the image @im, i.e.
      a Tree, where the value of each node is a 4-tuple of ints (can be 2 for some of the leafs),
      representing min-max of hierarchic boxes
      here minW and minH are the width, height of the minimal box
    """

    box_0 = im.getbbox()  # the initial box

    p = Node(box_0, None) # the root of the tree
    T = Tree( p )

    stack = [ p ]  # (4 ints, a tuple)

    W, H = abs(box_0[0] - box_0[2]), abs(box_0[1] - box_0[3])

    if ( (H <= minH) and (W <= minW) ):
        # we do not split further if the height and width are small enough
        return T


    while stack:
        x = stack.pop()
        x_box = x.value    # the box coordinates
        full_node = True   # shows if the x is full

        W, H = abs(x_box[0] - x_box[2]), abs(x_box[1] - x_box[3])
        if ( (H <= minH) and (W <= minW)):
            continue

        #consider the 4 sub-boxes:

        if (x_box[0] + x_box[2])%2 == 0:
            d1 = (x_box[0] + x_box[2])>>1
        else:
            d1 = (x_box[0] + x_box[2] + 1)>>1

        if (x_box[1] + x_box[3])%2 == 0:
            d2 = (x_box[1] + x_box[3])>>1
        else:
            d2 = (x_box[1] + x_box[3] + 1)>>1

        # (x0, x1, d1, x3), (d1+1, x1, x2, d2), (x0, d2+1, d1, x3), (d1+1, d2+1, x2, x3)

        #we now set the children of x
        if ((H > minH) and (W > minW) ):
            #we need 4 sub-rectangles

            x_child = (x_box[0], x_box[1], d1, d2 )
            if im.crop(x_child).getbbox() is not None:
                x.child1 = Node( x_child, x )
                stack.append(x.child1)
            else:
                full_node = False

            x_child = (d1 , x_box[1], x_box[2], d2)
            if im.crop(x_child).getbbox() is not None:
                x.child2 = Node( x_child,  x )
                stack.append(x.child2)
            else:
                full_node = False

            x_child = (x_box[0], d2, d1, x_box[3])
            if im.crop(x_child).getbbox() is not None:
                x.child3 = Node( x_child,  x )
                stack.append(x.child3)
            else:
                full_node = False

            x_child = (d1 , d2 , x_box[2], x_box[3])
            if im.crop(x_child).getbbox() is not None:
                x.child4 = Node( x_child,  x )
                stack.append(x.child4)
            else:
                full_node = False

            x.isFull = full_node

        else:
            if (( H <= minH  ) and ( W > minW ) ): # don't split the y-coord, but only x

                x_child = (x_box[0], x_box[1], d1, x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child1 = Node( x_child, x )
                    stack.append(x.child1)
                else:
                    full_node = False


                x_child = (d1, x_box[1], x_box[2], x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child2 = Node( x_child, x )
                    stack.append(x.child2)
                else:
                    full_node = False

                x.isFull = full_node

            else: #we're in a position that we only split H

                x_child = (x_box[0], x_box[1], x_box[2], d2 )
                if im.crop(x_child).getbbox() is not None:
                    x.child1 = Node( x_child, x )
                    stack.append(x.child1)
                else:
                    full_node = False

                x_child = (x_box[0], d2, x_box[2], x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child2 = Node( x_child, x )
                    stack.append(x.child2)
                else:
                    full_node = False


                x.isFull = full_node

    return T


cpdef insideCanvas( T, int shift0, int shift1, int W, int H ):
    """
     @T is the tree-representation of a word,
     @shift = (shift0, shift1) is the word's bounding box's upper-left corner coord on canvas
     @(W,H) = is the canvas_size

     returns True if the word's leaves stay inside the canvas
    """

    stack = [ T.root ]
    cdef int a, b, c, d

    while stack:
        v = stack.pop()

        a, b, c, d = v.value # a 4 tuple, left upper-coord and right-buttom coordinates
        if ( (a + shift0 < 0) or ( c + shift0 > W ) or (b + shift1 < 0) or (d + shift1 > H) ) == False:
            continue

        if v.isLeaf():
            return False

        stack += v.Children()

    return True



def collisionTest(T1, T2, shift1, shift2, stay_away):
    """
       the input is a pair of trees representing the objects as a quad-tree
       shift_1 = (a1, b1) and shift2 = (a2, b2) are the left-top coordinats of the boxes on the large canvas
       this means that all boxes in T_i must be shifted by (a_i, b_i), where i = 1, 2

       @stay_away parameter forces bounding boxes to stay at least @stay_away pixels away from each other

       return True iff the quad-trees have intersecting leaves, meaning the images they respresent actually intersect
    """

    r1, r2 = T1.root, T2.root

    if ( (not r1) or (not r2) ):
        return False


    stack = [ (r1, r2) ]

    while stack:
        p1, p2 = stack.pop()   # the nodes of the 1st and the 2nd trees

        #if intersectionRect(p1.value, p2.value, shift1, shift2, stay_away) == False:
        if intersectionRect_C(p1.value[0], p1.value[1], p1.value[2], p1.value[3], p2.value[0], p2.value[1], p2.value[2], p2.value[3], shift1[0], shift1[1], shift2[0], shift2[1], stay_away) == False:
            # if larger rectangles do not collide, their children will not collide either
            # hence no need to go for sub-nodes
            continue

        if ( p1.isLeaf() and p2.isLeaf() ):
            # leaves collide, we're done
            return True


        c1, c2 = p1.Children(), p2.Children()

        if not c1:
            for x in c2:
                stack.append( (p1, x) )
        else:
            if not c2:
                for x in c1:
                    stack.append( (x, p2) )
            else:
                # none are empty, i.e. the nodes are not leaves
                for x in c1:
                    for y in c2:
                        stack.append( (x, y) )


    return False
