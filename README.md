# Text Visualization Tools

Our aim with this repository is to develop tools for text visualization. As a warm-up, we start with by now a classical tool, called **wordle**. We implement it from scratch in Python 3 from the basic principles and relying on the approach outlined by the original creator of the wordle Jonathan Feinberg, see [this chapter](http://static.mrfeinberg.com/bv_ch03.pdf) for more details. As time permits, our plan is to gradually add more tools to this repository and enhance the existing ones.

For the time being, the code in [wordle](https://github.com/hayk314/visualization/tree/master/wordle) folder is an **end-to-end** implementation of the word cloud. One may speed up this program with some more work, but for now, we concentrate on a higher level details and leave such improvements for the future or for an interested Reader/User (who is very welcome to introduce improvements to this repository).

*This repository and this Readme file, in particular, are in their early days and are subject to change.*

## Wordle, what is it?

In short, wordle is a cloud made of words. Example is better than precept as they say. A cloud of words, a wordle,
created with the code from the [wordle](https://github.com/hayk314/visualization/tree/master/wordle) folder on a single chapter of Macbeth looks as follows:

![Wordle](https://github.com/hayk314/visualization/blob/master/sample_wordle.png)

## Sample usage

The input to the current version of the program is a text file. Download or clone this repository, install the missing python packages (see below) if any, then from a terminal window navigate to the [wordle](https://github.com/hayk314/visualization/tree/master/wordle) folder and call

`python wordle.py --fileName=fileName.txt`

where `fileName.txt` is the name of the text file you want to create the wordle from. If in need for **help** use 

`python wordle.py --help`

to see what are paramters of the program. Currently to call the program with the full list of parameters one should use this

`python wordle.py --fileName=sample.txt --verProb=0.1 --interactive=1`

where `vertProb` is the probability of a word to be placed vertically (can be anything from `[0,1]` with default value equal to `0`, i.e. all words will be placed *horizontally* if this paramter is skipped) and `interactive` is a boolean flag with `0,1` values allowing the user to repaint the final configuration of words as many times as they wish. If `interactive == 0` or it is skipped altogether, the program will create a single wordle image (word cloud) and will stop afterwards. Otherwise, if `interactive == 1` the program will ask the user if they want to apply other color schemes on the already created configuration. The prompting will continue until the user instructs the program to stop. In this way, if the configuration appears nice but not the coloring then there is still a chance to change the color scheme in a relatively cheap way. 

### Fonts and layout

To change the font of the words use the `fonts` folder and add your desired `true type` font there. Afterwards, change the `FONT_NAME` constant accordingly  in the `wordle.py` module. Here is another sample image with a different font:

![curlyFont](https://github.com/hayk314/visualization/blob/master/wordle/examples/research.png)

To get a black background with part of (or all) words placed vertically use ``--vertProb=0.1`` and ``--interactive=1`` . Here the ``0.1`` means that a probability of placing a word vertically is ``0.1``, this parameter can be anything between ``0`` - all horizontal and ``1`` - all vertical. The ``interactive`` is a boolean flag signaling the program to change layout colors at random until instructed by the user to stop. With these parameters one can get something that looks like this.

![blackBackground](https://github.com/hayk314/visualization/blob/master/wordle/examples/research-1.png)

## How this works, the algorithm

We briefly sketch the approach for creating wordles form text inputs. The entire process consists  of the following steps:

1. Tokenize the given file and compute the frequency  of each token
    - This is the first step of processing the textual input. We read a text file, strip off all the punctuation and consider each word, including those joined with a hyphen, as separate **tokens**, that is words to appear in the final cloud. We keep a separate list of **stop-words** (such as `and`, `but`,...) and remove these words from the list of tokens. The list of stop-words is a separate  file called `stop-words.txt` and one may change the list if necessary. We do not apply case-folding, however, we use some heuristic grouping rules, such as if a token appears both uppercase and lowercase in the text, we change the uppercase  versions to lowercase. We also replace the plurals of nouns with singulars, but in a rather crude way by just stripping off the last `s` from a token if the same token
appears without `s` in the text. For instance, if both `word` and `words` appear in the list of tokens, we replace all instances of `words` by `word`. Of course, one may use techniques from `natural language processing` (**NLP**) with the `nltk` module of python to work with the text in a more intelligent way. Applying **NLP** techniques, however, is not the primary goal in at the present.
All in all this step returns a list of tokens together with the frequencies at which they appear in the text, where tokens are sorted in decreasing order of their frequencies. This is the job of the file called `fileReader.py`.

2. Normalization of the tokens

    - The aim of normalization is to determine the font size of the final tokens. We let `m = min(frequency)`, `M = max(frequency)` and depending on the ratio `M/m`, we linearly scale the range `[m,M]` to some new range `[a,b]` in order to emphasize the effect of one word appearing more frequently than another. At this stage, we get a list of `Token` class instances where

    ```python
    class Token:
        """
            encapsulate the main information on a token into a single class
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
    ```

    We keep at most **400** tokens. This parameter is stored in `TOKENS_TO_USE` constant of `wordle.py` and can be changed. However, the larger the number of tokens the longer it takes to create the wordle image.


3. Placing the tokens on the canvas

    - This is the main part of the wordle creation: we get a list of tokens, and try to place them on an initially empty image (the *canvas*). For the placement strategy, we follow the [outline](http://static.mrfeinberg.com/bv_ch03.pdf) by the inventor of the wordle, Jonathan Feinberg. Recall that the tokens were sorted according to decreasing  frequencies. We start with an empty image and try to place the first token, i.e. the one with the biggest font size. For a word to image conversion, i.e. drawing the shape of the word on an image, we use Python's **PIL** library. Once the tokens are placed, they will not be moved. Assuming we have placed `n` tokens, for the `n+1`-th we choose its initial place randomly on the canvas, somewhere in the middle of the image, and keep moving it along some  **space-filling curve** (an *Archimedian spiral* or a *rectangular spiral*, one may also experiment with a *path of a symmetric random walk*, see below for more details) as long as it intersects any of the previously placed tokens. For an efficient way to check whether two separate word shapes intersect (notice that their bounding boxes might intersect, while the actual words are still collision free) we use [QuadTrees](https://en.wikipedia.org/wiki/Quadtree) to efficiently represent a word-shape as a tree of **hierarchical bounding boxes** (for more details see below). The function `placeWords` in `wordle.py` executes this placing strategy.


4. Drawing words on the canvas

    - This is the final part, when we have fixed the position of each word on the image and are ready to draw them. Having a list of tokens (see the `Token` class above) with `place` attributes filled by the previous step, and the corresponding canvas size determined, we simply draw these words with the given font sizes at the given `place` (upper-left corner coordinates of the bounding box of the word) on the canvas. A small wrinkle we need to take into account is that if some tokens were placed outside the proposed canvas area we need to increase the size of the canvas and update the places accordingly. It is also at this stage that we decide how to color each word. That part is delegated to `colorHandler.py`. As the last treat we offer, is changing the colors of the final cloud. Suppose the placement appears nice, but not the colors. Then if the `interactiveFlag` was set to `1` (True) then it is possible to keep repainting the existing configuration as long as necessary. The program prompts the user to either terminate the process or try a new color scheme.
At this stage we are done, the image is created successfully.

### Hierarchical bounding boxes

When placing word images on the canvas we need to have a way to decide if two shapes intersect or not to avoid overlaps.
An obvious way to prevent collisions of word shapes is to position the words such that their bounding boxes
(i.e. the smallest rectangle that contains the word) do not intersect.
This, however, is a rather crude condition and will force a lot of space around the words to stay unoccupied by words of smaller size.
We thus need to have a way to work with more or less the actual shapes of the words which do not have a nice
(from a computational perspective) representation.
A possible workaround here is to represent the images of words as a union of simpler shapes, such as small rectangles.
To this end, we use a well-known technique from computational geometry and represent words via hierarchical bounding boxes.
The interested reader is referred to [Quadtree](https://en.wikipedia.org/wiki/Quadtree) article on Wikipedia for a quick start.
Using hierarchical bounding boxes as a spatial index allows for quick checks whether two separate word shapes intersect or not.
The gain comes from the fact that the word is now represented as a relatively well balanced shallow tree of rectangles
and checking if two rectangles intersect is computationally very cheap.
We briefly outline how the tree is constructed. Start with a bounding box of the word and split it into four equal rectangles.
If any of these four rectangles does not contain part from the word, then drop it.
For the remaining rectangles repeat process of dividing into four sub-rectangles.
Stop the process if the diameter of the rectangle becomes smaller than some predefined threshold value.
In this way, we will get a tree of rectangles where the leaves of this tree represent a partition of a small neighbourhood of the word shape into disjoint rectangles.


Let us see this partition in action. Take some random word, say **SciLag**, draw this word on canvas (see the `drawWord` function in `wordle.py`) and create its Quadtree using the function `getQuadTree` in `BBox.py`. To visualize the actual partition we color the edges of all bounding boxes of this tree (see `tester.py`) and get something like this:

![QuadTree compressed](https://github.com/hayk314/visualization/blob/master/wordle/bbox_UNcompressed.png)

#### Compressing the tree

We gain a lot in computing time by compressing the QuadTrees. Assume a parent of a leaf node has all four children set. That means all four sub-rectangles of that parent rectangle contain a portion of the word shape, and the leaf is the "atomic"-rectangle (a pixel more or less) and cannot be split further. In this case, we could have stopped partitioning at the parent of these leaves without any loss of information. This is what we mean by the **tree compression**. We start from the leaves and if a leaf node has all its siblings defined we cancel the partition of the parent node. We repeat this pruning from bottom-up until we get to a non-complete set of siblings. Then the process stops. In doing this compression of the tree from bottom up we get to a tree that looks as follows.

![QuadTree](https://github.com/hayk314/visualization/blob/master/wordle/bbox_compressed.png)

As one can see this process got rid of many redundant information and made the tree smaller. It will save us a lot of computing time in the later usage of these trees.

#### Testing and experimenting with trees

The Trees described above are modelled, from an OOP perspective, in `Trees.py` and the main functions which utilize these trees, such as building for a given word shape, or checking if two shapes represented by trees collide or not are in `BBox.py`. We also devised a separate module for testing, called `tester.py`. To see more of the trees in action simply call

    python tester.py

 from the terminal and follow the instructions of the program.


## Spirals

Spirals are used for exploring the canvas. Namely, assume a word is placed at a certain coordinate `(x,y)` initially, but it intersects some of the already placed tokens. When trying new positions on the canvas for the word, we move it along some curve and for each point on the curve check if the place is valid, i.e. is collision-free. Ideally we would like this curves to be computationally cheap and have space-filling property, i.e. the trajectory of the curve should cover a significant portion of the canvas (if not the entire canvas itself). As a model example of such curves we try *Archimedian spiral* and *Rectangular spirals*, both are implemented in `Spirals.py`.


### Required packages of Python3

To make sure you have the necessary packages installed, `cd` to the directory containing the `requirments.txt` file and run the following command from your terminal window

    pip install -r requirments.txt

This will install a few packages listed in `requirments.txt`(which you would most probably have already).


### Author

`Hayk Aleksanyan`


### License

**MIT**, see the [License file](https://github.com/hayk314/visualization/blob/master/LICENSE)

### TODOs

While in its current form this wordle program does its job, there are some obvious directions one should try to improve it. The following list is not exhaustive.

- allow for non-horizontal placement of words
    - *UPDATE*: currently allowing vertical placements of words, the probability of tokens being placed vertically is part of the user input
- try moving some performance critical code into `C++` (or perhaps `cython` ?)
    - *UPDATE*: part of the code, most notably the placing strategy and part of collision checking now have `cython` equivalents. The gain in performance is substantial. See [cython version](https://github.com/hayk314/visualization/tree/master/wordle/cython_wordle) for more details.
- add a possibility of putting wordle into a predefined shape (a mask)
- allow for better font-scaling techniques
- propose a canvas size based on the tokens' sizes
- use NLP for more intelligent tokenization
