# Author: Hayk Aleksanyan
# create bounding hierarchical boxes for word shapes

from trees import QuadTreeNode, QuadTree


def rectangles_intersect(r1, r2, shift1=(0, 0), shift2=(0, 0), extraSize=3):
    """
        gets two 4-tuples of integers representing a rectangle in min, max coord-s
        optional params. @shifts can be used to move boxes on a larger canvas (2d plane)
                         @extraSize, forces the rectangles to stay away from each other
                         by the given size (number of pixels)

        returns True if the rectangles intersect
    """

    if ((min(r1[0] - extraSize + shift1[0], r1[2] + extraSize + shift1[0]) > max(r2[0] - extraSize + shift2[0],
                                                                                 r2[2] + extraSize + shift2[0]))
            or (max(r1[0] - extraSize + shift1[0], r1[2] + extraSize + shift1[0]) < min(r2[0] - extraSize + shift2[0],
                                                                                        r2[2] + extraSize + shift2[
                                                                                            0]))):
        return False

    if ((min(r1[1] - extraSize + shift1[1], r1[3] + extraSize + shift1[1]) > max(r2[1] - extraSize + shift2[1],
                                                                                 r2[3] + extraSize + shift2[1]))
            or (max(r1[1] - extraSize + shift1[1], r1[3] + extraSize + shift1[1]) < min(r2[1] - extraSize + shift2[1],
                                                                                        r2[3] + extraSize + shift2[
                                                                                            1]))):
        return False

    return True


def construct_quadtree(img, min_w, min_h):
    """
      returns the quad-tree representation of the image @im, i.e.
      a Tree, where the value of each node is a 4-tuple of ints (can be 2 for some of the leaves),
      representing min-max of hierarchic boxes
      here minW and minH are the width, height of the minimal box
    """

    box_0 = img.getbbox()  # the initial box

    quadtree_root = QuadTreeNode(box_0, None)
    quadtree = QuadTree(quadtree_root)

    stack = [quadtree_root]  # (4 ints, a tuple)

    w, h = abs(box_0[0] - box_0[2]), abs(box_0[1] - box_0[3])

    if (h <= min_h) and (w <= min_w):
        # we do not split further if the height and width are small enough
        return quadtree

    while stack:
        x = stack.pop()
        x_box = x.value  # the box coordinates
        full_node = True  # shows if the x is full

        w, h = abs(x_box[0] - x_box[2]), abs(x_box[1] - x_box[3])
        if (h <= min_h) and (w <= min_w):
            continue

        # consider the 4 sub-boxes:

        if (x_box[0] + x_box[2]) % 2 == 0:
            d1 = (x_box[0] + x_box[2]) >> 1
        else:
            d1 = (x_box[0] + x_box[2] + 1) >> 1

        if (x_box[1] + x_box[3]) % 2 == 0:
            d2 = (x_box[1] + x_box[3]) >> 1
        else:
            d2 = (x_box[1] + x_box[3] + 1) >> 1

        # (x0, x1, d1, x3), (d1+1, x1, x2, d2), (x0, d2+1, d1, x3), (d1+1, d2+1, x2, x3)

        # we now set the children of x
        if (h > min_h) and (w > min_w):
            # we need 4 sub-rectangles

            x_child = (x_box[0], x_box[1], d1, d2)
            if img.crop(x_child).getbbox() is not None:
                x.child1 = QuadTreeNode(x_child, x)
                stack.append(x.child1)
            else:
                full_node = False

            x_child = (d1, x_box[1], x_box[2], d2)
            if img.crop(x_child).getbbox() is not None:
                x.child2 = QuadTreeNode(x_child, x)
                stack.append(x.child2)
            else:
                full_node = False

            x_child = (x_box[0], d2, d1, x_box[3])
            if img.crop(x_child).getbbox() is not None:
                x.child3 = QuadTreeNode(x_child, x)
                stack.append(x.child3)
            else:
                full_node = False

            x_child = (d1, d2, x_box[2], x_box[3])
            if img.crop(x_child).getbbox() is not None:
                x.child4 = QuadTreeNode(x_child, x)
                stack.append(x.child4)
            else:
                full_node = False

            x.node_is_full = full_node

        else:
            if (h <= min_h) and (w > min_w):  # don't split the y-coord, but only x

                x_child = (x_box[0], x_box[1], d1, x_box[3])
                if img.crop(x_child).getbbox() is not None:
                    x.child1 = QuadTreeNode(x_child, x)
                    stack.append(x.child1)
                else:
                    full_node = False

                x_child = (d1, x_box[1], x_box[2], x_box[3])
                if img.crop(x_child).getbbox() is not None:
                    x.child2 = QuadTreeNode(x_child, x)
                    stack.append(x.child2)
                else:
                    full_node = False

                x.node_is_full = full_node

            else:  # we're in a position that we only split H

                x_child = (x_box[0], x_box[1], x_box[2], d2)
                if img.crop(x_child).getbbox() is not None:
                    x.child1 = QuadTreeNode(x_child, x)
                    stack.append(x.child1)
                else:
                    full_node = False

                x_child = (x_box[0], d2, x_box[2], x_box[3])
                if img.crop(x_child).getbbox() is not None:
                    x.child2 = QuadTreeNode(x_child, x)
                    stack.append(x.child2)
                else:
                    full_node = False

                x.node_is_full = full_node

    return quadtree


def is_inside_canvas(quadtree, shift, canvas_size):
    """
     @T is the tree-representation of a word,
     @shift is the word's bounding box's upper-left corner coord on canvas
     @canvas_size is a tuple (width, height) of the canvas

     returns True if the word's leaves stay inside the canvas
    """

    stack = [quadtree.root]
    w, h = canvas_size
    sh_w, sh_h = shift

    while stack:
        v = stack.pop()

        a, b, c, d = v.value  # a 4 tuple, left upper-coord and right-bottom coordinates
        if not ((a + sh_w < 0) or (c + sh_w > w) or (b + sh_h < 0) or (d + sh_h > h)):
            continue

        if v.is_leaf():
            return False

        stack += v.get_children_list()

    return True


def test_collision(quadtree1, quadtree2, shift1, shift2, stay_away):
    """
       the input is a pair of trees representing the objects as a quad-tree
       shift_1 = (a1, b1) and shift2 = (a2, b2) are the left-top coordinates of the boxes on the large canvas
       this means that all boxes in T_i must be shifted by (a_i, b_i), where i = 1, 2

       @stay_away parameter forces bounding boxes to stay at least @stay_away pixels away from each other

       return True iff the quad-trees have intersecting leaves, meaning the images they respresent actually intersect
    """

    r1, r2 = quadtree1.root, quadtree2.root

    if (not r1) or (not r2):
        return False

    stack = [(r1, r2)]

    while stack:
        p1, p2 = stack.pop()  # the nodes of the 1st and the 2nd trees

        if not rectangles_intersect(p1.value, p2.value, shift1, shift2, stay_away):
            # if larger rectangles do not collide, their children will not collide either
            # hence no need to go for sub-nodes
            continue

        if p1.is_leaf() and p2.is_leaf():
            # leaves collide, we're done
            return True

        c1, c2 = p1.get_children_list(), p2.get_children_list()

        if not c1:
            for x in c2:
                stack.append((p1, x))
        else:
            if not c2:
                for x in c1:
                    stack.append((x, p2))
            else:
                # none are empty, i.e. the nodes are not leaves
                for x in c1:
                    for y in c2:
                        stack.append((x, y))

    return False
