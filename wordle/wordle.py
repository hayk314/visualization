# Designed and implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

import argparse

import os
from PIL import Image, ImageFont, ImageDraw, ImageOps
import random
import timeit

import spirals
import bbox
import color_handler
import tokenizer

# constants:
TOKENS_TO_USE = 400  # number of different tokens to use in the wordle
STAY_AWAY = 2  # force any two words to stay at least this number of pixels away from each other
FONT_SIZE_MIN = 10  # the smallest font of a word
FONT_SIZE_MAX = 300  # the largest font of a word, might go slightly above this value
DESIRED_HW_RATIO = 0.618  # height/widht ratio of the canvas
QUADTREE_MINSIZE = 5  # minimal height-width of the box in quadTree partition
FONT_NAME = os.path.join("fonts", "OLDENGL.TTF")  # the font (true type) used to draw the word shapes


class Token:
    """
        Token models a word to be placed on a canvas for the final wordle image.
    """

    def __init__(self, word, font_size=10, draw_at_angle=0):
        self.word = word
        self.font_size = font_size  # an integer
        self.draw_at_angle = draw_at_angle  # integer representing the rotation angle of the image; 0 - for NO rotation
        self.img_size = None  # integers (width, height) size of the image of this word with the given fontSize
        self.quadtree = None  # the quadTree of the image of this word with the above characteristics
        self.place = None  # tuple, the coordinate of the upper-left corner of the token on the final canvas
        self.color = None  # the fill color on canvas (R, G, B) triple


class Wordle:
    def __init__(self, file_path, vert_prob=0.0):
        self.file_path = file_path
        self.vert_prob = vert_prob

        self._arch_spiral_param = 0.2
        self._rect_spiral_param = 2

    @property
    def name(self):
        return type(self).__name__

    def propose_canvas_w_h(self):
        """ more advanced methods can be used to suggest a canvas size based on the size of tokens to be used """
        return 3000, 1500

    @staticmethod
    def get_random_flips(n, p):
        """
         Return an array of length n of random bits {0, 1} where Probability(0) = p and Probability(1) = 1 - p
         this is used for randomly selecting some of the tokens for vertical placement.
        """
        ans = n * [0]
        for i in range(n):
            x = random.random()
            if x > p:
                ans[i] = 1

        return ans

    def create_normalized_tokens(self, token_to_freq, N_of_tokens_to_use, horizontal_prob=1.0):
        """
         (linearly) scale the font sizes of tokens to a new range depending on the ratio of the current min-max
         and take maximum @N_of_tokens_to_use of these tokens
         allow some words to have vertical orientation defined by @horizontal_prob
        """

        token_to_freq_tuples = list(token_to_freq.items())[:N_of_tokens_to_use]
        words = [a for (a, _) in token_to_freq_tuples]
        sizes = [b for (_, b) in token_to_freq_tuples]

        normal_tokens = []  # the list of Tokens to be returned

        # scale the range of sizes; the scaling rules applied below are fixed from some heuristic considerations
        # the user of this code is welcome to apply their own reasoning

        a, b = min(sizes), max(sizes)
        print('[{}] the ratio of MAX font-size over MIN={}'.format(self.name, b / a), flush=True)
        if a == b:
            sizes = len(sizes) * [30]
        else:
            if b <= 8 * a:
                m1, m2 = 15, 1 + int(20 * b / a)
            elif b <= 16 * a:
                m1, m2 = 14, 1 + int(18 * b / a)
            elif b <= 32 * a:
                m1, m2 = 13, 1 + int(9 * b / a)
            elif b <= 64 * a:
                m1, m2 = 11, 1 + int(4.7 * b / a)
            else:
                m1, m2 = FONT_SIZE_MIN, FONT_SIZE_MAX

            sizes = [int(((m2 - m1) / (b - a)) * (x - a) + m1) for x in sizes]

        print('[{}] after scaling of fonts min={}, max={}'.format(self.name, min(sizes), max(sizes)), '\n')

        # allow some vertical placement; the probability is defined by the user
        flips = Wordle.get_random_flips(len(words), horizontal_prob)
        for i in range(len(sizes)):
            normal_tokens.append(Token(words[i], sizes[i], 0 if flips[i] == 0 else 90))

        return normal_tokens

    @staticmethod
    def draw_word(token, use_color=False):
        """
          gets an instance of Token class and draws the word it represents
          returns an image of the given word in the given font size
          the image is NOT cropped
        """

        font = ImageFont.truetype(FONT_NAME, token.font_size)
        w, h = font.getsize(token.word)

        im = Image.new('RGBA', (w, h), color=None)
        draw = ImageDraw.Draw(im)
        if not use_color:
            draw.text((0, 0), token.word, font=font)
        else:
            draw.text((0, 0), token.word, font=font, fill=token.color)

        if token.draw_at_angle != 0:
            im = im.rotate(token.draw_at_angle, expand=1)

        return im

    @staticmethod
    def draw_on_canvas(normal_tokens, canvas_size):
        """
           given a list of tokens and a canvas size, we put the token images onto the canvas
           the places of each token on this canvas has already been determined during placeWords() call.

           Notice, that it is not required that the @place of each @token is inside the canvas;
           if necessary we may enlarge the canvas size to embrace these missing images
        """

        c_w, c_h = canvas_size  # the suggested canvas size, might change here

        # there can be some positions of words which fell out of the canvas
        # we first need to go through these exceptions (if any) and expand the canvas and (or) shift the coordinate's origin.

        x_min, y_min = 0, 0

        for i, token in enumerate(normal_tokens):
            if token.place is None:
                continue

            if x_min > token.place[0]:
                x_min = token.place[0]
            if y_min > token.place[1]:
                y_min = token.place[1]

        x_shift, y_shift = 0, 0
        if x_min < 0:
            x_shift = -x_min
        if y_min < 0:
            y_shift = -y_min

        x_max, y_max = 0, 0
        for i, token in enumerate(normal_tokens):
            if token.place is None:
                continue

            token.place = (token.place[0] + x_shift, token.place[1] + y_shift)
            if x_max < token.place[0] + token.img_size[0]:
                x_max = token.place[0] + token.img_size[0]
            if y_max < token.place[1] + token.img_size[1]:
                y_max = token.place[1] + token.img_size[1]

        c_w = max(c_w, x_max)
        c_h = max(c_h, y_max)

        im_canvas = Image.new('RGBA', (c_w + 10, c_h + 10), color=None)
        im_canvas_white = Image.new('RGBA', (c_w + 10, c_h + 10), color=(255, 255, 255, 255))

        # decide the background color with a coin flip; 0 -for white; 1 - for black (will need brighter colors)
        background = random.randint(0, 1)

        # add color to each word to be placed on canvas, pass on the background info as well
        color_handler.add_color_to_tokens(normal_tokens, background)

        for i, token in enumerate(normal_tokens):
            if token.place is None:
                print('the word <' + token.word + '> was skipped', flush=True)
                continue

            im = Wordle.draw_word(token, use_color=True)
            if background == 0:
                im_canvas_white.paste(im, token.place, im)
            else:
                im_canvas.paste(im, token.place, im)

        margin_size = 10  # the border margin size
        if background == 0:
            r, g, b, a = im_canvas_white.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            box = ImageOps.invert(rgb_img).getbbox()
            if box is None:
                box = (0, 0, margin_size, margin_size)
        else:
            box = im_canvas.getbbox()

        if background == 0:
            # white background
            im_canvas_1 = Image.new('RGBA', (box[2] - box[0] + 2 * margin_size, box[3] - box[1] + 2 * margin_size),
                                    color=(100, 100, 100, 100))
            im_canvas_1.paste(im_canvas_white.crop(box),
                              (margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1]))
        else:
            # black background
            im_canvas_1 = Image.new('RGB', (box[2] - box[0] + 2 * margin_size, box[3] - box[1] + 2 * margin_size),
                                    color=(0, 0, 0))
            im_canvas_1.paste(im_canvas.crop(box),
                              (margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1]))

        return im_canvas_1

    @staticmethod
    def create_quadtrees(normal_tokens):
        """
            given a list of tokens we fill their quadTree attributes and cropped image size
        """

        for i, token in enumerate(normal_tokens):
            im_tmp = Wordle.draw_word(token)
            quadtree = bbox.construct_quadtree(im_tmp, QUADTREE_MINSIZE, QUADTREE_MINSIZE)
            quadtree.compress()
            im_tmp = im_tmp.crop(im_tmp.getbbox())

            token.quadtree = quadtree
            token.img_size = im_tmp.size

    def place_words(self, normal_tokens):
        """
          gets a list of tokens and their frequencies
          executes the placing strategy and
          returns canvas size, locations of upper-left corner of words and words' sizes
        """

        # 1. we first create the QuadTrees for all words and determine a size for the canvas

        word_img_path = []  # shows the path passed through the spiral before hitting a free space

        print('[{}] number of tokens={}'.format(self.name, len(normal_tokens)), flush=True)

        t_start = timeit.default_timer()

        # create the quadTrees and collect sizes (width, height) of the cropped images of the words
        Wordle.create_quadtrees(normal_tokens)

        t_stop = timeit.default_timer()
        print('[{}] (i)  quadTrees were created for all words in {} seconds'.format(self.name, t_stop - t_start),
              flush=True)

        # 2. We now find places for the words on our canvas
        c_w, c_h = self.propose_canvas_w_h()

        print('[{}] (ii) trying to place the words\n'.format(self.name), flush=True)

        t_start = timeit.default_timer()

        # 3a. we start with the 1st word

        ups_and_downs = [random.randint(0, 10) % 2 for _ in range(len(normal_tokens))]

        for i, token in enumerate(normal_tokens):
            print(token.word, end=' ', flush=True)

            # determine a starting position on the canvas of this token, near half of the width of canvas
            w, h = random.randint(int(0.3 * c_w), int(0.7 * c_w)), (c_h >> 1) - (token.img_size[1] >> 1)
            if w < 0 or w >= c_w:
                w = c_w >> 1
            if h < 0 or h >= c_h:
                h = c_h >> 1

            direction = 2 * (random.randint(0, 10) % 2) - 1  # 1, -1; randomness to the placing strategy
            if ups_and_downs[i] == 0:
                spiral_gen = spirals.Archimedian(direction * self._arch_spiral_param).generator
            else:
                spiral_gen = spirals.Rectangular(self._rect_spiral_param, direction).generator

            location1 = (w, h)

            word_img_path.append((w, h))

            last_hit_index = 0  # we cache the index of last hit

            iter_ = 0

            start_countdown = False
            max_iter = 0

            for dx, dy in spiral_gen:
                w, h = location1[0] + dx, location1[1] + dy

                if start_countdown:
                    max_iter -= 1
                    if max_iter == 0:
                        break
                else:
                    iter_ += 1

                if w < 0 or w >= c_w or h < 0 or h > c_h:
                    #  the shape has fallen outside the canvas
                    if not start_countdown:
                        start_countdown = True
                        max_iter = 1 + 10 * iter_

                location1 = (w, h)
                collision = False

                if last_hit_index < i:
                    j = last_hit_index
                    if normal_tokens[j].place is not None:
                        collision = bbox.test_collision(token.quadtree, normal_tokens[j].quadtree, location1,
                                                        normal_tokens[j].place, STAY_AWAY)

                if not collision:
                    # NO collision with the cached index
                    for j in range(i):  # check for collisions with the rest of the tokens
                        if (j != last_hit_index) and (normal_tokens[j].place is not None):
                            if bbox.test_collision(token.quadtree, normal_tokens[j].quadtree, location1,
                                                   normal_tokens[j].place,
                                                   STAY_AWAY):
                                collision = True
                                last_hit_index = j

                                break  # no need to check with the rest of the tokens, try a new position now

                if not collision:
                    if bbox.is_inside_canvas(token.quadtree, location1, (c_w, c_h)):
                        # at this point we have found a place inside the canvas where the current token has NO collision
                        # with the already placed tokens; The search has been completed.
                        token.place = location1
                        break  # breaks the spiral movement
                    else:
                        if token.place is None:
                            # even though this place is outside the canvas, it is collision free and we
                            # store it in any case to ensure that the token will be placed
                            token.place = location1

        t_stop = timeit.default_timer()

        print('\n[{}] words were placed in {} seconds'.format(self.name, t_stop - t_start),  flush=True)

        return c_w, c_h

    def create(self, interactive=False):
        """ the master function, creates the wordle from a given text file """

        tk = tokenizer.SimpleTokenizer(stop_words_file="stop-words.txt")
        tokens = tk.tokenize_file(self.file_path, token_min_length=2)
        token_to_freq = tk.get_token_to_freq_sorted(tokens, drop_stop_words=True)

        normal_tokens = self.create_normalized_tokens(token_to_freq, TOKENS_TO_USE, 1.0 - self.vert_prob)
        canvas_w, canvas_h = self.place_words(normal_tokens)

        wordle_img = Wordle.draw_on_canvas(normal_tokens, (canvas_w, canvas_h))

        wordle_file_path = filepath[0:-4] + '_wordle.png'
        wordle_img.save(wordle_file_path)
        print('the wordle image was successfully saved on the disc as <{}>'.format(wordle_file_path), flush=True)

        if interactive:
            # we allow the user to repaint the existing tokens with other color schemes as many times as they wish
            print('\n=========== You may repaint the existing wordle with other color schemes =========== \n')
            print('To stop, please type the text inside the quotes: "q" followed by Enter')
            print('To try a new scheme type any other char\n')

            version = 1
            while True:
                ans = input(str(version) + '.   waiting for new user input ... ')
                if 'q' == ans:
                    print('exiting...')
                    break

                wordle_img = Wordle.draw_on_canvas(normal_tokens, (canvas_w, canvas_h))
                wordle_file_path = filepath[0:-4] + '_wordle_v' + str(version) + '.png'
                wordle_img.save(wordle_file_path)
                print('=== saved on the disc as <{}>'.format(wordle_file_path), flush=True)
                version += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Processing arguments for wordle.')
    parser.add_argument('--filepath', type=str, required=True,
                        help='path of the text file on which the world will be build')
    parser.add_argument('--vertprob', type=float, required=False, default=0.0,
                        help='probability of a word to be placed vertically; default placement is horizontal')
    parser.add_argument('--interactive', type=bool, required=False, default=False,
                        help='if 1, will not exit after wordle creation to allow change of color schemes')

    args = parser.parse_args()

    filepath = args.filepath
    vertprob = args.vertprob
    interactive = args.interactive

    if vertprob < 0.0:
        vertprob = 0.0
    if vertprob > 1.0:
        vertprob = 1.0

    wordle = Wordle(filepath, vertprob)
    wordle.create(interactive=interactive)

