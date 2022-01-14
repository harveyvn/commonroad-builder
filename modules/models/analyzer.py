import cv2
import imutils
import numpy as np
import matplotlib.pyplot as plt
from math import floor, ceil
from modules import slice_when, angle
from .road import Road
from modules.roadlane.laneline import Laneline


class Analyzer:
    def __init__(self, image, lanelines: [Laneline], road: Road):
        self.image = image
        self.lanelines = lanelines
        self.road = road

    def draw_img_with_baselines(self, ax):
        ax.imshow(self.image, cmap='gray')
        colors = ["red", "green", "blue", "purple"]
        for i, line in enumerate(self.lanelines):
            ax.plot([p[0] for p in line.coords],
                    [p[1] for p in line.coords],
                    color=colors[i])
        return ax

    def draw_img_with_roi(self, ax):
        xs, ys = self.road.poly.exterior.xy
        ax.imshow(self.image, cmap='gray')
        ax.plot(xs, ys, c="red")
        return ax

    def draw_img(self, ax, masked_img):
        ax.imshow(masked_img, cmap='gray')
        return ax

    def draw_histogram(self, ax, hist, peaks: [] = None):
        ax.plot([i for i in range(0, len(hist))], hist)
        if len(peaks) > 0:
            for peak in peaks:
                plt.plot(peak, hist[peak], '.', color="red")
        return ax

    def run(self):
        """
        Detect lanelines from a region of interest
        """
        fig, ax = plt.subplots(2, 3, figsize=(16, 24))
        axs = []

        ax[0, 0].title.set_text("Step 01")
        axs.append(self.draw_img_with_baselines(ax[0, 0]))

        ax[0, 1].title.set_text("Step 02")
        axs.append(self.draw_img_with_roi(ax[0, 1]))

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
        # Debug
        ax[0, 2].title.set_text("Step 03")
        axs.append(self.draw_img(ax[0, 2], masked_img))

        # Crop an image
        crop_img = masked_img[ymin:ymax, xmin:xmax]
        # Debug
        ax[1, 0].title.set_text("Step 04")
        axs.append(self.draw_img(ax[1, 0], crop_img))

        # Rotate the crop image
        # Find the angle for rotation
        lineA = [list(self.road.mid_line.coords)[0], list(self.road.mid_line.coords)[-1]]
        lineB = [[0, 0], [1, 0]]
        difference = 90 - angle(lineA, lineB)
        # Rotate our image by certain degrees around the center of the image
        rotated_img = imutils.rotate_bound(crop_img, -difference)
        # Debug:
        ax[1, 1].title.set_text("Step 05")
        axs.append(self.draw_img(ax[1, 1], rotated_img))

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
        axs.append(self.draw_histogram(ax[1, 2], hist))
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

        self.road.angle = difference
        return self.road
