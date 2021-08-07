# Author: Hayk Aleksanyan
# testing wordle related utils
# anything in this module is for illustration/test purposes only

import inspect
from PIL import Image, ImageFont, ImageDraw
from termcolor import colored
import timeit

import bbox


def color_bbox_borders(im, quadtree, shift=(0, 0)):
    """
        takes an image @im and a Tree @quadtree corresponding to the bounding box hierarchy (quad-tree partition)
        colors only the borders of bounding rectangles
    """

    w = 1  # the (symmetric) width of the border of rectangles to be colored

    im_1 = im.copy()
    (W, H) = im_1.size

    boxes = quadtree.get_node_value_list()

    for z in boxes:

        for u in range(z[0] + shift[0], z[2] + shift[0]):
            for v in range(z[1] + shift[1] - w, z[1] + shift[1] + w + 1):
                if (v >= 0) and (v < H):
                    im_1.putpixel((u, v), (255, 0, 0, 0))

            for v in range(z[3] + shift[1] - w, z[3] + shift[1] + w + 1):
                if (v >= 0) and (v < H):
                    im_1.putpixel((u, v), (255, 0, 0, 0))

        for u in range(z[1] + shift[1], z[3] + shift[1]):
            for v in range(z[0] + shift[0] - w, z[0] + shift[0] + w + 1):
                if (v >= 0) and (v < W):
                    im_1.putpixel((v, u), (255, 0, 0, 0))

            for v in range(z[2] + shift[0] - w, z[2] + shift[0] + w + 1):
                if (v >= 0) and (v < W):
                    im_1.putpixel((v, u), (255, 0, 0, 0))

    return im_1


def color_boxes(im, boxes, shift=(0, 0)):
    """
       gets an image @im and a list of rectangles (in upper-left - bottom-right coordinates) @Boxes
       @shift parameter can be used to shift the rectangles in the coordinate system.

       This function colors bounding boxes @Boxes of the image @im in red and returns this colored image
    """
    im_1 = im.copy()

    for i in range(len(boxes)):
        z = boxes[i].value
        for u in range(z[0] + shift[0], z[2] + shift[0]):
            for v in range(z[1] + shift[1], z[3] + shift[1]):
                im_1.putpixel((u, v), (255, 0, 0, 0))

    return im_1


def draw_word(test_word, font_size):
    """ returns the cropped image of the @word with Font.size = @font_size """

    font = ImageFont.truetype("fonts/arial.ttf", font_size)
    w, h = font.getsize(test_word)

    img = Image.new('RGBA', (w, h), color=None)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), test_word, font=font)

    box_0 = img.getbbox()  # the initial bounding box
    img = img.crop(box_0)

    return img


def test_quadtrees(test_word="test", font_size=200):
    """ create quadtree of the given test-word  with a given font size, and apply tree compression (pruning)
       save the images of colored bounding boxes
    """

    t_start = timeit.default_timer()

    im = draw_word(test_word, font_size)
    t_stop = timeit.default_timer()
    print('1. Image of word [{}] build in {} seconds'.format(test_word, t_stop - t_start), flush=True)

    t_start = timeit.default_timer()

    quadtree_of_word = bbox.construct_quadtree(im, 7, 7)

    t_stop = timeit.default_timer()
    print('2. Quad tree constructed in {} seconds'.format(t_stop - t_start), flush=True)

    t_start = timeit.default_timer()

    im_colored_boxes = color_bbox_borders(im, quadtree_of_word)

    t_stop = timeit.default_timer()
    print('3. Coloring of the uncompressed tree took {} seconds'.format(t_stop - t_start), flush=True)

    t_start = timeit.default_timer()
    quadtree_of_word.compress()
    t_stop = timeit.default_timer()
    print('4. Tree compression done in {} seconds'.format(t_stop - t_start), flush=True)

    t_start = timeit.default_timer()

    im_color_boxes_pruned = color_bbox_borders(im, quadtree_of_word)

    t_stop = timeit.default_timer()
    print('5. Coloring of the compressed tree took {} seconds'.format(t_stop - t_start), flush=True)

    # convert RGBA to RGB allowing the files to be saved as png
    im_colored_boxes_back = Image.new('RGB', im_colored_boxes.size, (0, 0, 0))
    im_colored_boxes_back.paste(im_colored_boxes)

    im_color_boxes_pruned_back = Image.new('RGB', im_color_boxes_pruned.size, (0, 0, 0))
    im_color_boxes_pruned_back.paste(im_color_boxes_pruned)

    bbox_img_file_name = test_word + '_BBox.png'
    bbox_pruned_img_file_name = test_word + '_pruned_BBox.png'

    im_colored_boxes_back.save(bbox_img_file_name)
    im_color_boxes_pruned_back.save(bbox_pruned_img_file_name)

    print('The outputs were saved on [{}] and [{}]'.format(bbox_img_file_name, bbox_pruned_img_file_name), flush=True)


def try_to_get_spiral_class_by_alias(alias):
    """ try to get the spiral class by its alias """

    spiral_module = __import__("spirals")
    spiral_cls = None

    for name, obj in inspect.getmembers(spiral_module):
        if inspect.isclass(obj):
            if hasattr(obj, "get_alias") and obj.get_alias() == alias:
                spiral_cls = obj
                break

    return spiral_cls


def get_spiral_aliases():
    spiral_module = __import__("spirals")

    spiral_aliases = []

    for name, obj in inspect.getmembers(spiral_module):
        if inspect.isclass(obj):
            if hasattr(obj, "get_alias"):
                if obj.get_alias() != "":
                    spiral_aliases.append(obj.get_alias())

    return spiral_aliases


def test_spirals(spiral_alias, param, n_of_iter=1000, snapshot_freq=200):

    spiral_cls = try_to_get_spiral_class_by_alias(spiral_alias)
    if spiral_cls is None:
        print("the spiral alias [{}] was not recognized.".format(spiral_alias), flush=True)
        return

    spiral_cls_inst = spiral_cls(param)

    img = spiral_cls_inst.draw(1000, 1000, n_of_iter, snapshot_freq=snapshot_freq)
    file_name = spiral_cls_inst.name + '_iter=' + str(n_of_iter) + '.png'
    img.save(file_name)
    print('The spiral image saved on ', file_name, flush=True)


def testing_directive():
    """ start a process of testing, prompting the user until they wish to terminate """

    print('\nStarting testing process of QuadTrees and Spirals.')

    avail_spiral_alias_set = get_spiral_aliases()
    avail_spiral_aliases = ", ".join(list(avail_spiral_alias_set))

    while True:
        msg = "\nType 1 - for {}, 2 - for {}: anything else will terminate\n".format(
            colored("QuadTrees", "blue", attrs=["bold"]), colored("Spirals", "blue", attrs=["bold"]))
        ans = input(msg)
        if ans != '1' and ans != '2':
            print('exiting...')
            return

        if ans == '1':
            test_word = input('please type the word to build the QuadTree on\n')
            if len(test_word) == 0:
                print('empty string, nothing to do\n')
                continue
            elif len(test_word) > 100:
                print('please restrict the input to maximum 100 characters\n')
                continue

            font_size = input('please type the font size, an integer between 1 and 1000\n')
            if not font_size.isdigit():
                print('the input is not an integer, nothing to do')
                continue

            font_size = int(font_size)
            if not 0 < font_size <= 1000:
                print('please keep the font size between 1 and 1000')
                continue

            test_quadtrees(test_word=test_word, font_size=font_size)

        if ans == '2':
            spiral_alias = input('type any of these [{}] spiral aliases\n'.format(avail_spiral_aliases))
            if spiral_alias not in avail_spiral_alias_set:
                print("the alias is not recognized", flush=True)
                continue

            param = input('please type the parameter of the spiral\n')
            try:
                param = float(param)
            except:
                print('the parameter must be numeric')
                continue

            if param <= 0:
                print('the parameter must be positive\n')
                continue

            n_of_iter = input('please type the number of iterations\n')
            if not n_of_iter.isdigit() or int(n_of_iter) <= 0:
                print('the iteration number must be positive\n')
                continue
            n_of_iter = int(n_of_iter)

            test_spirals(spiral_alias, param, n_of_iter=n_of_iter)


if __name__ == "__main__":
    # simply follow the prompt of the program
    testing_directive()
