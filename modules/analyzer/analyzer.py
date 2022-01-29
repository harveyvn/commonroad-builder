import cv2
import imutils
import numpy as np
from .visualization import Visualization
from math import floor, ceil
from shapely import affinity
from shapely.geometry import Point, LineString
from modules import slice_when, angle
from modules.common import translate_ls_to_new_origin
from modules.constant import CONST
from modules.roadlane.laneline import Laneline
from modules.models import Road, LaneMarking


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
        image (numpy.ndarray): an processed image taken from CRISCE.
        lanelines ([Laneline]): a list of middle lanelines (visualization purpose only).
        road (Road): a road object will be analyzed.
    """

    def __init__(self, image, lanelines: [Laneline], road: Road):
        self.image = image
        self.road = road
        self.visualization = Visualization(image, lanelines, road)

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
        viz_images["masked_img"] = masked_img

        # Crop an image
        xmin = xmin if xmin > 0 else 0
        ymin = ymin if ymin > 0 else 0
        crop_img = masked_img[ymin:ymax, xmin:xmax]
        viz_images["crop_img"] = crop_img

        # Rotate the crop image
        # Find the angle for rotation
        lineA = [list(self.road.mid_line.coords)[0], list(self.road.mid_line.coords)[-1]]
        lineB = [[0, 0], [1, 0]]
        difference = 90 - angle(lineA, lineB)
        # Rotate our image by certain degrees around the center of the image
        rotated_img = imutils.rotate_bound(crop_img, -difference)
        viz_images["rotated_img"] = rotated_img

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

            # Take first 7 points from a line string
            if len(checked_coords) < 3:
                window_line = LineString(coords)
            else:
                window_line = LineString(checked_coords[0:7])
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
            else:
                invalid_lines.append({"i": i, "lst": lst, "total": total})
            i = i + 1

        # Debug:
        sorted_lines = (valid_lines + invalid_lines).copy()
        self.visualization.draw_searching(sorted_lines, valid_lines, rotated_img, True)

        # Return a dictionary composing list of x values and their density values
        xs_dict = {}
        for line in valid_lines:
            xs_dict[line["i"]] = line["total"]

        viz_images["xs_dict"] = xs_dict
        return xs_dict

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

        # Compare a total value of each x value to find a peak
        peaks = []
        for group in groups:
            chosen_peak = group[0]
            for x in group:
                if lane_dict[x] > lane_dict[chosen_peak]:
                    chosen_peak = x
            peaks.append(chosen_peak)
        viz_images["peaks"] = peaks

        # Left boundary is on the left hand side and right boundary is on the right hand side of the list
        lane_markings = list()
        road_width = peaks[-1] - peaks[0]
        for i, peak in enumerate(peaks):
            # Compute the ratio of the lane from the left boundary - aka blue line
            ratio = ((peak - peaks[0]) / road_width)
            width = groups[i][-1] - groups[i][0]
            lane_markings.append(LaneMarking(ratio, width))

        # Find the minimum lane width
        widths = set()
        for lane in lane_markings:
            widths.add(lane.width)

        # Categorize the lane type based on its width
        for i, lane in enumerate(lane_markings):
            # Left or right boundary.
            if i == 0 or i == len(lane_markings) - 1:
                if min(widths) <= lane.width < 1.8 * min(widths):
                    lane.type = CONST.SINGLE_LINE
                else:
                    lane.type = CONST.DOUBLE_LINE
            else:
                # Other lanes.
                if min(widths) <= lane.width < 1.8 * min(widths):
                    lane.type = CONST.SINGLE_DASHED_LINE
                else:
                    lane.type = CONST.DOUBLE_DASHED_LINE

        # Flip the case when an angle between a middle line and Ox > -1 and < 1 degree
        # and the left x is greater than the right x.
        if -1 < self.road.angle < 1:
            left_boundary_x = list(self.road.left_boundary.coords)[0][0]
            right_boundary_x = list(self.road.right_boundary.coords)[0][0]
            if left_boundary_x > right_boundary_x:
                for i, lane in enumerate(lane_markings[1:-1]):
                    lane.type = lane_markings[-1-i]

        # Assign the lanes to the road
        self.road.lane_markings = lane_markings

    def visualize(self):
        # Visualization: Draw a histogram to find the starting points of lane lines
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 3, figsize=(16, 24))
        axs = [
            self.visualization.draw_img_with_baselines(ax[0, 0], "Step 01"),
            self.visualization.draw_img_with_roi(ax[0, 1], "Step 02"),
            self.visualization.draw_img(ax[0, 2], viz_images["masked_img"], "Step 03"),
            self.visualization.draw_img(ax[1, 0], viz_images["crop_img"], "Step 04"),
            self.visualization.draw_img(ax[1, 1], viz_images["rotated_img"], "Step 05"),
            self.visualization.draw_histogram(ax[1, 2], viz_images["rotated_img"],
                                              viz_images["xs_dict"], viz_images["peaks"], "Step 06")
        ]
        plt.show()
