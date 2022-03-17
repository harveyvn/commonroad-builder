import cv2
import imutils
import numpy as np
from .winline import Winline
from .visualization import Visualization
from .lib import create, find, analyze, define_roi
from math import floor, ceil
from typing import List
from shapely import affinity
from shapely.geometry import Point, LineString
from modules import slice_when, angle
from modules.common import translate_ls_to_new_origin, reverse_geom, smooth_line, get_dbscan_labels
from modules.constant import CONST
from modules.roadlane.laneline import Laneline
from modules.models import Segment, Line

viz_images = {
    "masked_img": None,
    "crop_img": None,
    "rotated_img": None,
    "lines": [],
    "peaks": [],
    "before_rotate": [],
    "after_rotate": []
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
        self.angle = 0

    def del_oor_lines(self):
        # Define list contain out of range lines
        oor_lines = dict()
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
                    oor_lines[step] = Winline(id=step, points=list(window_line.coords))
                    step = step + 1
                    break

            if invalid_line is False:
                stop = True

        return step, oor_lines

    def find_lines(self, starting_x, outlier_threshold, num_points: int = 10):
        good_lines, bad_lines = dict(), dict()
        first_x_valid, starting_color_index = -1, 0
        img, ls = self.rotated_img, self.rotated_ls

        # Searching the valid lane ids from remaining lines
        x = starting_x
        while x < img.shape[1]:
            expected_num_points = num_points + starting_color_index
            window_line = create(img=img, point_x=x, ls=ls, num_points=expected_num_points)
            coords = [(ceil(p[0]), ceil(p[1])) for p in list(window_line.coords[starting_color_index:])]

            # Compute the white density from a pixel image
            total, points = 0, list()
            for p in coords:
                try:
                    total += int(img[p[1], p[0]])
                    points.append(p)
                except IndexError:
                    pass

            # Remove outliers from window line
            if len(points) > 1 and outlier_threshold > 0:
                fpoints = []
                labels = get_dbscan_labels(X=points, distance=outlier_threshold)
                for l, p in zip(labels, points):
                    if l > -1:
                        fpoints.append(p)
                points = fpoints

            if total > 0:
                length, non_zeros, zeros = analyze(points=points, img=img)
                if zeros / length >= CONST.MAX_PERCENTAGE_ZEROS:
                    bad_lines[x] = Winline(id=x, points=list(window_line.coords))
                else:
                    # Look for index of the first point has color value bigger than 0 in the first valid line
                    # Take that index as a base index and use it on other lines to find line type
                    if first_x_valid == -1:
                        first_x_valid = x
                        starting_color_index = find(points=points, img=img)
                        continue
                    good_lines[x] = Winline(id=x, points=points, total=total, zero_perc=zeros / length)
            else:
                bad_lines[x] = Winline(id=x, points=list(window_line.coords))
            x = x + 1

        return good_lines, bad_lines

    def search_laneline(self, num_points: int = 10, outlier_threshold: int = 0, debug: bool = False):
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
        alpha = 0
        if -3 <= angle(lineA, lineB) <= 3:
            alpha = 0
        if 175 <= angle(lineA, lineB) <= 185:
            alpha = 180
        if 85 <= angle(lineA, lineB) <= 95:
            alpha = 90
        if -95 <= angle(lineA, lineB) <= -85:
            alpha = -90
        difference = 90 - alpha
        # Rotate our image by certain degrees around the center of the image
        self.rotated_img = imutils.rotate_bound(crop_img, -difference)

        # Rotate the baseline by certain degree following the image rotation
        self.rotated_ls = affinity.rotate(self.segment.mid_line, -difference, (0, 0))
        self.angle = -difference
        self.segment.angle = -difference

        # Find the starting valid x, so that the window line will not be out of range e.g. oor
        first_x, oor_lines = self.del_oor_lines()
        good_lines, bad_lines = self.find_lines(starting_x=first_x, num_points=num_points, outlier_threshold=outlier_threshold)

        # Debug:
        # if len(oor_lines.keys()) > 0:
        #     bad_lines = [bad_lines.append(line) for line in oor_lines]
        if debug:
            self.visualization.draw_searching([], good_lines, self.rotated_img, True)

        viz_images["crop_img"] = crop_img
        viz_images["rotated_img"] = self.rotated_img
        return good_lines

    def categorize_laneline(self, lane_dict):
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

        # Define thickness
        thickness = max([len(g) for g in groups])
        # Generating corresponding lines
        lines = [Line(thickness=thickness,
                      marks=dict(filter(lambda i: i[0] in group, lane_dict.items()))) for group in groups]

        # Assign the lanes to the road
        lsts, lstrs = list(), list()
        if self.segment.kind == CONST.ROAD_CURVE_OR_STRAIGHT:
            peaks = [l.get_peak() for l in lines]
            sel_boundary = self.segment.right_boundary if self.segment.is_horizontal else self.segment.left_boundary
            sel_side = "right"
            # Default
            if self.segment.is_vertical is False and self.segment.is_horizontal is False:
                sel_boundary = self.segment.left_boundary

            # Process
            sel_lsr = affinity.rotate(sel_boundary, self.angle, (0, 0))
            # Splitting to a fixed number of points
            distances = np.linspace(0, sel_lsr.length, 10)
            points = [sel_lsr.interpolate(distance) for distance in distances]
            sel_lsr = LineString(points)
            for i, line in enumerate(lines):
                distance = line.get_peak() - peaks[0] if i > 0 else 0.000001
                ls = reverse_geom(sel_lsr.parallel_offset(distance=distance, side=sel_side, join_style=2))
                lsr = affinity.rotate(ls, -self.angle, (0, 0))
                lsts.append(ls)
                lstrs.append(lsr)
        elif self.segment.kind == CONST.ROAD_PARALLEL:
            first, last = self.rotated_ls.boundary
            for i, line in enumerate(lines):
                ls = translate_ls_to_new_origin(self.rotated_ls, Point(line.get_peak(), first.y))
                lsr = affinity.rotate(ls, -self.angle, (0, 0))
                lsts.append(ls)
                lstrs.append(lsr)

        viz_images["lines"] = lines
        viz_images["before_rotate"] = lsts
        viz_images["after_rotate"] = lstrs

        assert len(lstrs) == len(lines)
        for i, line in enumerate(lines):
            line.ls = lstrs[i]
        return lines

    def visualize(self, title: str = None, is_save: bool = False, debug: bool = False):
        # Visualization: Draw a histogram to find the starting points of lane lines
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(5, 2, figsize=(16, 24))
        axs = [
            self.visualization.draw_img_with_baselines(ax[0, 0], "Step 01: Baseline"),
            self.visualization.draw_img_with_roi(ax[0, 1], "Step 02: ROI"),
            self.visualization.draw_img(ax[1, 0], viz_images["masked_img"], "Step 03: Masked"),
            self.visualization.draw_img(ax[1, 1], viz_images["crop_img"], "Step 04: Crop"),
            self.visualization.draw_img(ax[2, 0], viz_images["rotated_img"], "Step 05: Rotate"),
            self.visualization.draw_lines_on_image(ax[2, 1], viz_images["rotated_img"], viz_images["before_rotate"],
                                                   "Step 06", viz_images["lines"], True),
            self.visualization.draw_lines_on_image(ax[3, 0], self.image, viz_images["after_rotate"], "Step 07",
                                                   viz_images["lines"], True),
            self.visualization.draw_lines_on_image(ax[3, 1], self.image, viz_images["after_rotate"], "Step 07 no image",
                                                   viz_images["lines"]),
            self.visualization.draw_segment_lines(ax[4, 0], viz_images["after_rotate"], "Step 08",
                                                  viz_images["lines"], True),
            self.visualization.draw_segment_lines(ax[4, 1], viz_images["after_rotate"], "Step 08 no image",
                                                  viz_images["lines"])
            # self.visualization.draw_histogram(ax[1, 2], viz_images["rotated_img"], viz_images["xs_dict"], viz_images["peaks"], "Step 06")
        ]
        plt.show()
        if is_save:
            fig.savefig(f'{title}.png', bbox_inches="tight")

        if debug:
            for l in viz_images["lines"]:
                print(l)
            exit()