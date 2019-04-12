# Author: Hayk Aleksanyan
# create and test Trees for spatial partition



def rectArea(r):
    # returns the area of the rectangle given in min-max coordinates (top-left <--> bottom-right)
    return abs( (r[0] - r[2])*(r[1] - r[3]) )


class Node:
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

        self.isFull = False # shows if the node has maximum number of children
                            # i.e. has reached its full capacity (2 or 4 in our case)

        self.child1 = None
        self.child2 = None
        self.child3 = None
        self.child4 = None

    def isLeaf(self):
        # true, if this node is a leaf, i.e. has no children
        return ( (self.child1 is None) and (self.child2 is None) and (self.child3 is None) and (self.child4 is None) )

    def Children(self):
        # return the list of children, if any
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

    def hasLeaf_ChildrenOnly(self):
        # True, if the all children of this node (if any) are leaves
        if (self.child1 is not None):
            if self.child1.isLeaf() == False:
                return False

        if (self.child2 is not None):
            if self.child2.isLeaf() == False:
                return False

        if (self.child3 is not None):
            if self.child3.isLeaf() == False:
                return False

        if (self.child4 is not None):
            if self.child4.isLeaf() == False:
                return False

        return True


class Tree:
    """
      stores the entire quad-tree partition, where each member of the partition is a Node class
    """

    def __init__(self, root):
        # root is a Node; serves as the root of this tree
        self.root = root

    def getLeafs(self):
        #returns the leafs of the tree as a list

        if self.root == None:
            return []

        res = []

        c = self.root.Children()
        while c:
            c1 = []
            for x in c:
                if x.isLeaf():
                    res.append(x)
                else:
                    for u in x.Children():
                        c1.append(u)

            c = c1

        return res

    def nodeCount(self):
        # returns the leafs of the tree as a list

        if self.root == None:
            return 0

        res = 1
        c = self.root.Children()

        while c:
            c1 = []
            res += len(c)

            for x in c:
                #print(' '*i + 'Level ' + str(i) + ' : ' + str(x.value) )
                if x.isLeaf() == False:
                    for u in x.Children():
                        c1.append(u)

            c = c1

        return res


    def getValues(self, output = False):
        """
          traverses the tree T from the root to its leaves and returns a list of all values of all nodes
          if output == True, prints the values
        """

        if self.root == None:
            if output == True:
                print('The tree is empty')
            return []

        res = [ self.root.value ]

        c = self.root.Children()
        i = 0

        while c:
            i += 1
            c1 = []
            for x in c:
                if output == True:
                    print(' '*i + 'Level ' + str(i) + ' : ' + str(x.value) )

                res.append(x.value)
                if not x.isLeaf():
                    for u in x.Children():
                        c1.append(u)

            c = c1

        return res


    def compress(self):
        """
         compresses the tree T by removing all leaves whose siblings
         are leafs and whose parents have reached their full (child) capacity,
         i.e. have MAX number of children (2 or 4 in our case)
         performs this process from bottom-up until there is nothing to remove
        """

        if self.root == None:
            return

        current_level = [ self.root ]
        all_nodes = [ [current_level] ]

        while True:
            c = []
            for i in range( len(current_level) ):
                x = current_level[i]
                if x.child1 != None:
                    c.append(x.child1)
                if x.child2 != None:
                    c.append(x.child2)
                if x.child3 != None:
                    c.append(x.child3)
                if x.child4 != None:
                    c.append(x.child4)

            if c == []:
                break

            all_nodes.append(c)
            current_level = c[:]


        for i in range( len( all_nodes ) -1, 0, -1 ):
            for j in range( len( all_nodes[i] ) ):
                n = all_nodes[i][j]

                if n != None:
                    p = n.parent
                    if p.isFull:
                        # p has all 4 or all 2 children
                        if p.hasLeaf_ChildrenOnly():
                            # compression means that we destroy all children of a node
                            # with only leaf children and where all child nodes are occupied
                            p.child1 = None
                            p.child2 = None
                            p.child3 = None
                            p.child4 = None



    def areaCovered( self ):
        """
          compute the numerical value of the 2d area covered by this Tree
          the object represented by this tree is the disjoin union of its leaves;
          leaves are rectangles, thus we need to compute the sum of the areas of these rectangles
        """

        a = 0
        c = self.getLeafs()

        for r in c:
            a += rectArea(r.value)

        return a
