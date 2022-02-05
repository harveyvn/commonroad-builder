import cv2
import imutils
import numpy as np
from .visualization import Visualization
from math import floor, ceil
from typing import List
from shapely import affinity
from shapely.geometry import Point, LineString
from .common import create, find, analyze, define_roi
from modules import slice_when, angle
from modules.common import translate_ls_to_new_origin
from modules.constant import CONST
from modules.roadlane.laneline import Laneline
from modules.models import Segment, LaneMarking

viz_images = {
    "masked_img": None,
    "crop_img": None,
    "rotated_img": None,
    "xs_dict": {},
    "peaks": []
}


class Analyzer:
    """
    The Analyzer class accepts extracted road data from CRISCE module, then search the possible position of
    lane lines within the road and categorize the lane type.

    Args:
        image (numpy.ndarray): a processed image taken from CRISCE.
        lanelines ([Laneline]): a list of middle lanelines (visualization purpose only).
        segment (Segment): a road object will be analyzed.
    """

    def __init__(self, image: np.array, lanelines: [Laneline], segment: Segment):
        self.image = image
        self.segment = segment
        self.visualization = Visualization(image, lanelines, segment)
        self.rotated_img = None
        self.rotated_ls = None

    def del_oor_lines(self):
        # Define list contain out of range lines
        oor_lines = list()
        step, stop = 0, False
        img, ls = self.rotated_img, self.rotated_ls

        # Searching invalid lines
        while stop is False:
            window_line = translate_ls_to_new_origin(ls, Point(step, 0))
            if list(window_line.coords)[-1][1] < 0:
                window_line = translate_ls_to_new_origin(ls, Point(step, img.shape[0]))

            # Check if x value of all points (from a line string)
            # is in an x-axis range of a rotated image or not.
            # Otherwise, the linestring is invalid.
            invalid_line = False
            for point in list(window_line.coords):
                if point[0] < 0:
                    invalid_line = True
                    oor_lines.append({"i": step, "points": list(window_line.coords)})
                    step = step + 1
                    break

            if invalid_line is False:
                stop = True

        return step, oor_lines

    def find_lines(self, starting_x, num_points: int = 10):
        img, ls = self.rotated_img, self.rotated_ls
        first_x_valid, starting_color_index = -1, 0
        good_lines, bad_lines = list(), list()

        # Searching the valid lane ids from remaining lines
        x = starting_x
        while x < img.shape[1]:
            expected_num_points = num_points + starting_color_index
            window_line = create(img=img, point_x=x, ls=ls, num_points=expected_num_points)
            coords = [(ceil(p[0]), ceil(p[1])) for p in list(window_line.coords[starting_color_index:])]

            # Compute the white density from a pixel image
            points = list()
            total = 0
            for p in coords:
                points.append(p)
                try:
                    total += int(img[p[1], p[0]])
                except IndexError:
                    pass

            if total > 0:
                # Look for index of the first point has color value bigger than 0 in the first valid line
                # Take that index as a base index and use it on other lines to find line type
                if first_x_valid == -1:
                    first_x_valid = x
                    starting_color_index = find(points=points, img=img)
                    continue

                length, non_zeros, zeros = analyze(points=points, img=img)
                if zeros / length >= CONST.MAX_PERCENTAGE_ZEROS:
                    bad_lines.append({"i": x, "points": points})
                else:
                    line_type = "dash" if zeros / length > CONST.MAX_PERCENTAGE_ZEROS_CONT else "cont"
                    good_lines.append({"i": x, "points": points, "total": total,
                                       "type": line_type, "percentage": zeros / length})
            else:
                bad_lines.append({"i": x, "points": points})
            x = x + 1

        return good_lines, bad_lines

    def search_laneline(self):
        """
        Search lane lines by defining a region within an image, then crop the region
        and measure the density of non-black pixels.

        Return:
            lane_dict (dict):   a dictionary contains all possible lane position and its pixel density value
            inside a road, including left/right boundaries. An example of lane_dict is:
            {
                41: 367, 42: 1179, 43: 327, 44: 112,  // 1st lane
                105: 43, 106: 555, 107: 940, 108: 1020,  // 2nd lane
                176: 207, 177: 858, 178: 993, 179: 239  // 3rd lane
            }
        """

        # Define the bounding rectangle
        # Region of Interest (ROI) to be cropped
        xs, ys = self.segment.poly.exterior.xy
        xmin, xmax = floor(min(xs)), ceil(max(xs))
        ymin, ymax = floor(min(ys)), ceil(max(ys))
        roi_area = define_roi(xmin, xmax, ymin, ymax)

        # Create a mask using poly points
        # Create a mask with white pixels
        mask = np.ones(self.image.shape, dtype=np.uint8)
        mask.fill(255)
        cv2.fillPoly(mask, np.int32([roi_area]), 0)
        # Applying the mask to original image
        masked_img = cv2.bitwise_or(self.image, mask)
        viz_images["masked_img"] = masked_img

        # Crop an image
        xmin = xmin if xmin > 0 else 0
        ymin = ymin if ymin > 0 else 0
        crop_img = masked_img[ymin:ymax, xmin:xmax]

        # Rotate the crop image
        # Find the angle for rotation
        lineA = [list(self.segment.mid_line.coords)[0], list(self.segment.mid_line.coords)[-1]]
        lineB = [[0, 0], [1, 0]]
        difference = 90 - angle(lineA, lineB)
        # Rotate our image by certain degrees around the center of the image
        self.rotated_img = imutils.rotate_bound(crop_img, -difference)

        # Rotate the baseline by certain degree following the image rotation
        self.rotated_ls = affinity.rotate(self.segment.mid_line, -difference, (0, 0))

        # Find the starting valid x, so that the window line will not be out of range e.g. oor
        first_x, oor_lines = self.del_oor_lines()
        good_lines, bad_lines = self.find_lines(starting_x=first_x)

        # Debug:
        # if len(oor_lines) > 0:
        #     bad_lines = [bad_lines.append(line) for line in oor_lines]
        # self.visualization.draw_searching(bad_lines, good_lines, self.rotated_img, True)

        # Return a dictionary composing list of x values and their density values
        xs_dict = {}
        for line in good_lines:
            xs_dict[line["i"]] = line["total"]

        viz_images["crop_img"] = crop_img
        viz_images["rotated_img"] = self.rotated_img
        viz_images["xs_dict"] = xs_dict
        return xs_dict, good_lines

    def categorize_laneline(self, lane_dict, lane_markings, threshold=300):
        """
        Take the width of different lane lines and suggest the suitable type for each lane.
        The type might be: a single line, a dashed line, a double line or a double dashed line.

        Args: lane_dict (dict):   a dictionary contains all possible lane position and its pixel density value
        inside a road, including left/right boundaries. The format of lane_dict might be:
            {
                41: 367, 42: 1179, 43: 327, 44: 112,  // 1st lane
                105: 43, 106: 555, 107: 940, 108: 1020,  // 2nd lane
                176: 207, 177: 858, 178: 993, 179: 239  // 3rd lane
            }

        Returns:
            A list of lane object.
        """
        # Grouping x-values which form a line
        groups = list(slice_when(lambda x, y: y - x > 2, list(lane_dict.keys())))

        for group in groups:
            lines = []
            percs = []
            for line_id in group:
                for line in lane_markings:
                    if line['i'] == line_id:
                        lines.append(line["type"])
                        percs.append(line["percentage"])
            print(f'{group} : {lines} : {percs}')

        # Assign the lanes to the road
        self.segment.lane_markings = []

    def visualize(self):
        # Visualization: Draw a histogram to find the starting points of lane lines
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 3, figsize=(16, 24))
        axs = [
            self.visualization.draw_img_with_baselines(ax[0, 0], "Step 01"),
            self.visualization.draw_img_with_roi(ax[0, 1], "Step 02"),
            self.visualization.draw_img(ax[0, 2], viz_images["masked_img"], "Step 03"),
            self.visualization.draw_img(ax[1, 0], viz_images["crop_img"], "Step 04"),
            self.visualization.draw_img_1(ax[1, 1], viz_images["rotated_img"], "Step 05"),
            # self.visualization.draw_histogram(ax[1, 2], viz_images["rotated_img"], viz_images["xs_dict"], viz_images["peaks"], "Step 06")
        ]
        plt.show()
