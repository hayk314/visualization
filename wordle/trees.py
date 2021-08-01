# Author: Hayk Aleksanyan
# create and test Trees for spatial partition


def get_rectangle_area(r):
    # returns the area of the rectangle given in min-max coordinates (top-left <--> bottom-right)
    return abs((r[0] - r[2]) * (r[1] - r[3]))


class QuadTreeNode:
    """
      used to model a rectangle in quad-tree partition of the 2d plane;
      each Node models a rectangle in the partition and can have at most 4 sub-rectanlges
      representing the members of quad-tree construction
      the value of the node is a 4-tuple of integers representing a rectangle
      in "left upper-coord, and right-buttom" form
    """

    def __init__(self, val, p):
        self.value = val
        self.parent = p  # is a Node  or None if this is the root

        self.node_is_full = False  # shows if the node has maximum number of children
        # i.e. has reached its full capacity (2 or 4 in our case)

        self.child1 = None
        self.child2 = None
        self.child3 = None
        self.child4 = None

    def is_leaf(self):
        """ true, if and only if this node is a leaf, i.e. has no children """
        return (self.child1 is None) and (self.child2 is None) and (self.child3 is None) and (self.child4 is None)

    def get_children_list(self):
        """ return the list of children nodes, if any, otherwise an empty list """

        c = []
        if self.child1 is not None:
            c.append(self.child1)
        if self.child2 is not None:
            c.append(self.child2)
        if self.child3 is not None:
            c.append(self.child3)
        if self.child4 is not None:
            c.append(self.child4)

        return c

    def all_children_are_leafs(self):
        """ True, if and only if no child of this node is a non-leaf node """

        if self.child1 is not None:
            if not self.child1.is_leaf():
                return False

        if self.child2 is not None:
            if not self.child2.is_leaf():
                return False

        if self.child3 is not None:
            if not self.child3.is_leaf():
                return False

        if self.child4 is not None:
            if not self.child4.is_leaf():
                return False

        return True


class QuadTree:
    """
      stores the entire quad-tree partition, where each member of the partition is an instance of QuadTreeNode
    """

    def __init__(self, root):
        """ root is a QuadTreeNode that serves as the root of this tree """
        self.root = root

    def get_leaf_list(self):
        """ returns the leaves of the tree as a list """

        if self.root is None:
            return []

        res = []

        c = self.root.get_children_list()
        while c:
            c1 = []
            for x in c:
                if x.is_leaf():
                    res.append(x)
                else:
                    for u in x.get_children_list():
                        c1.append(u)

            c = c1

        return res

    def get_number_of_nodes(self):
        """ get the total number of nodes of this tree """

        if self.root is None:
            return 0

        res = 1
        c = self.root.get_children_list()

        while c:
            c1 = []
            res += len(c)

            for x in c:
                if not x.is_leaf():
                    for u in x.get_children_list():
                        c1.append(u)

            c = c1

        return res

    def get_node_value_list(self, output=False):
        """
          traverses the tree T from the root to its leaves and returns a list of all values of all nodes
          if output == True, print the values
        """

        if self.root is None:
            if output:
                print('The tree is empty', flush=True)
            return []

        res = [self.root.value]

        c = self.root.get_children_list()
        i = 0

        while c:
            i += 1
            c1 = []
            for x in c:
                if output:
                    print("{} level {} : {}".format(' ' * i, i, x.value), flush=True)

                res.append(x.value)
                if not x.is_leaf():
                    for u in x.get_children_list():
                        c1.append(u)

            c = c1

        return res

    def compress(self):
        """
         Compresses the tree T by removing all leaves whose siblings
         are leafs and whose parents have reached their full capacity,
         i.e. have MAX number of children (2 or 4 in our case).
         Performs this process from bottom-up until there is nothing to remove.
        """

        if self.root is None:
            return

        current_level = [self.root]
        nodes_at_level = [[current_level]]

        while True:
            c = []
            for i in range(len(current_level)):
                x = current_level[i]
                if x.child1 is not None:
                    c.append(x.child1)
                if x.child2 is not None:
                    c.append(x.child2)
                if x.child3 is not None:
                    c.append(x.child3)
                if x.child4 is not None:
                    c.append(x.child4)

            if not c:
                break

            nodes_at_level.append(c)
            current_level = c[:]

        for i in range(len(nodes_at_level) - 1, 0, -1):
            for n in nodes_at_level[i]:
                if n is None:
                    continue

                p = n.parent
                if p.node_is_full:
                    # p has all 4 or all 2 children
                    if p.all_children_are_leafs():
                        # compression means that we destroy all children of a node
                        # with only leaf children and where all child nodes are occupied
                        p.child1 = None
                        p.child2 = None
                        p.child3 = None
                        p.child4 = None

    def area_covered(self):
        """
          compute the numerical value of the 2d area covered by this Tree
          the object represented by this tree is the disjoint union of its leaves;
          leaves are rectangles, thus we need to compute the sum of the areas of these rectangles
        """

        a = 0
        c = self.get_leaf_list()

        for r in c:
            a += get_rectangle_area(r.value)

        return a
