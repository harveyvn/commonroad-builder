import cv2
import imutils
import numpy as np
import matplotlib.pyplot as plt
from math import floor, ceil
from shapely.geometry import Polygon
from modules import slice_when, angle


class Analyzer:
    def __init__(self, poly: Polygon, image, baseline, roads):
        self.poly = poly
        self.image = image
        self.baseline = baseline
        self.roads = roads

    def run(self):
        """
        Detect lanelines from a region of interest
        """
        fig, ax = plt.subplots(2, 3, figsize=(16, 24))
        axs = []

        ax[0, 0].title.set_text("Step 01")
        ax[0, 0].imshow(self.image, cmap='gray')
        colors = ["red", "green", "blue", "purple"]
        for i, road in enumerate(self.roads):
            ax[0, 0].plot([p[0] for p in road.coords],
                          [p[1] for p in road.coords],
                          color=colors[i])
        axs.append(ax[0, 0])

        ax[0, 1].title.set_text("Step 02")
        xs, ys = self.poly.exterior.xy
        # Debug:
        ax[0, 1].imshow(self.image, cmap='gray')
        ax[0, 1].plot(xs, ys, c="red")
        axs.append(ax[0, 1])

        # Define the bounding rectangle
        # Region of Interest (ROI) to be cropped
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
        # Debug
        ax[0, 2].title.set_text("Step 03")
        ax[0, 2].imshow(masked_img, cmap='gray')
        axs.append(ax[0, 2])

        # Crop an image
        crop_img = masked_img[ymin:ymax, xmin:xmax]
        # Debug
        ax[1, 0].title.set_text("Step 04")
        ax[1, 0].imshow(crop_img, cmap='gray')
        axs.append(ax[1, 0])

        # Rotate the crop image
        # Find the angle for rotation
        lineA = [self.baseline[0], self.baseline[-1]]
        lineB = [[0, 0], [1, 0]]
        difference = 90 - angle(lineA, lineB)
        # Rotate our image by certain degrees around the center of the image
        rotated_img = imutils.rotate_bound(crop_img, -difference)
        # Debug:
        ax[1, 1].title.set_text("Step 05")
        ax[1, 1].imshow(rotated_img, cmap='gray')
        axs.append(ax[1, 1])

        # Find a histogram
        hist = None
        cutoffs = [int(rotated_img.shape[0] / 2), 0]
        for cutoff in cutoffs:
            hist = np.sum(rotated_img[cutoff:, :], axis=0)
            if hist.max() > 0:
                break
        if hist.max() == 0:
            print('Unable to detect lane lines in this frame. Trying another frame!')
            return False, np.array([]), np.array([])
        # Debug:
        ax[1, 2].title.set_text("Step 06")
        ax[1, 2].plot([i for i in range(0, len(hist))], hist)
        axs.append(ax[1, 2])
        plt.show()

        threshold = 5500
        peaks = []
        for i, val in enumerate(hist):
            if val > threshold:
                peaks.append(i)
        print(f'Possible peaks: {peaks}')

        tst = peaks.copy()
        slices = list(slice_when(lambda x, y: y - x > 2, tst))
        print(f'Slice peaks: {slices}')
        peaks = []
        for slice in slices:
            chosen_peak = slice[0]
            for ind in slice:
                if hist[ind] > hist[chosen_peak]:
                    chosen_peak = ind
            peaks.append(chosen_peak)
        print(f'Chosen peaks: {peaks}')

        plt.plot([i for i in range(0, len(hist))], hist)
        for peak in peaks:
            plt.plot(peak, hist[peak], '.', color="red")
        plt.show()
