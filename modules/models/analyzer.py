import cv2
import imutils
import numpy as np
from .road import Road
from .viz_analyzer import VizAnalyzer
from math import floor, ceil
from shapely import affinity
from shapely.geometry import Point, LineString
from modules import slice_when, angle
from modules.common import translate_ls_to_new_origin
from modules.roadlane.laneline import Laneline


class Analyzer:
    def __init__(self, image, lanelines: [Laneline], road: Road):
        self.image = image
        self.lanelines = lanelines
        self.road = road
        self.visualization = VizAnalyzer(image, lanelines, road)

    def run(self):
        """
        Detect lanelines from a region of interest
        """

        # Define the bounding rectangle
        # Region of Interest (ROI) to be cropped
        xs, ys = self.road.poly.exterior.xy
        xmin, xmax = floor(min(xs)), ceil(max(xs))
        ymin, ymax = floor(min(ys)), ceil(max(ys))
        roi_area = np.array([[(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]], dtype=np.int32)

        # Create a mask using poly points
        # Create a mask with white pixels
        mask = np.ones(self.image.shape, dtype=np.uint8)
        mask.fill(255)
        cv2.fillPoly(mask, np.int32([roi_area]), 0)
        # Applying the mask to original image
        masked_img = cv2.bitwise_or(self.image, mask)

        # Crop an image
        crop_img = masked_img[ymin:ymax, xmin:xmax]

        # Rotate the crop image
        # Find the angle for rotation
        lineA = [list(self.road.mid_line.coords)[0], list(self.road.mid_line.coords)[-1]]
        lineB = [[0, 0], [1, 0]]
        difference = 90 - angle(lineA, lineB)
        # Rotate our image by certain degrees around the center of the image
        rotated_img = imutils.rotate_bound(crop_img, -difference)

        # Visualization: Draw a histogram to find the starting points of lane lines
        #
        # fig, ax = plt.subplots(2, 3, figsize=(16, 24))
        # axs = [self.visualization.draw_img_with_baselines(ax[0, 0], "Step 01"),
        #        self.visualization.draw_img_with_roi(ax[0, 1], "Step 02"),
        #        self.visualization.draw_img(ax[0, 2], masked_img, "Step 03"),
        #        self.visualization.draw_img(ax[1, 0], crop_img, "Step 04"),
        #        self.visualization.draw_img(ax[1, 1], rotated_img, "Step 05"),
        #        self.visualization.draw_histogram(ax[1, 2], rotated_img, "Step 06", True)]
        # plt.show()

        self.road.angle = -difference
        rotated_lst = affinity.rotate(self.road.mid_line, self.road.angle, (0, 0))
        # Define variables:
        # i is a x value, in range (0, rotated_img.shape[1]), aka an end of a rotated image x-axis
        i = 0
        is_stop = False
        invalid_lines, valid_lines = list(), list()

        # Searching invalid lines
        while is_stop is False:
            window_line = translate_ls_to_new_origin(rotated_lst, Point(i, 0))
            if list(window_line.coords)[-1][1] < 0:
                window_line = translate_ls_to_new_origin(rotated_lst, Point(i, rotated_img.shape[0]))

            # Check if x value of all points (from a line string)
            # is in a x range of a rotated image or not. Otherwise, the linestring is invalid.
            invalid_line = False
            for p in list(window_line.coords):
                if p[0] < 0:
                    invalid_line = True
                    invalid_lines.append({"i": i, "lst": list(window_line.coords)})
                    i = i + 1
                    break

            if invalid_line is False:
                is_stop = True

        # Searching the valid lane ids from remaining lines
        while i < rotated_img.shape[1]:
            window_line = translate_ls_to_new_origin(rotated_lst, Point(i, 0))
            if list(window_line.coords)[-1][1] < 0:
                window_line = translate_ls_to_new_origin(rotated_lst, Point(i, rotated_img.shape[0]))
            # Remove a point not in a rotated image
            coords, checked_coords = list(window_line.coords[0:20]), []
            for p in coords:
                try:
                    if int(rotated_img[int(p[1]), int(p[0])]) > -1:
                        checked_coords.append(p)
                except IndexError:
                    pass

            # Take first 3 points from a line string
            window_line = LineString(checked_coords[0:3])
            coords = [(floor(p[0]), floor(p[1])) for p in list(window_line.coords)]

            # Compute the white density from a pixel image
            lst = list()
            total = 0
            for p in coords:
                lst.append(p)
                try:
                    total += int(rotated_img[p[1], p[0]])
                except IndexError:
                    pass

            if total > 0:
                valid_lines.append({"i": i, "lst": lst, "total": total})
            i = i + 1

        # Debug:
        # self.visualization.draw_searching(invalid_lines, valid_lines, rotated_img)

        # Grouping x-values which form a line
        xs_dict = {}
        for line in valid_lines:
            xs_dict[line["i"]] = line["total"]
        groups = list(slice_when(lambda x, y: y - x > 2, list(xs_dict.keys())))

        # Compare a total value of each x value to find a peak
        peaks = []
        for group in groups:
            chosen_peak = group[0]
            for x in group:
                if xs_dict[x] > xs_dict[chosen_peak]:
                    chosen_peak = x
            peaks.append(chosen_peak)

        print(f'Peaks: {peaks}')
        print(groups)
        print(xs_dict)
