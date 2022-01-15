import numpy as np
from modules import slice_when
from modules.models import Road
from modules.roadlane.laneline import Laneline
import matplotlib.pyplot as plt


class Visualization:
    def __init__(self, image, lanelines: [Laneline], road: Road):
        self.image = image
        self.lanelines = lanelines
        self.road = road

    def draw_img_with_baselines(self, ax, title):
        ax.title.set_text(title)
        ax.imshow(self.image, cmap='gray')
        colors = ["red", "green", "blue", "purple"]
        for i, line in enumerate(self.lanelines):
            ax.plot([p[0] for p in line.coords],
                    [p[1] for p in line.coords],
                    color=colors[i])
        return ax

    def draw_img_with_lines(self, ax, lines, title):
        ax.title.set_text(title)
        ax.imshow(self.image, cmap='gray')
        colors = ["red", "green", "blue", "purple"]
        for i, line in enumerate(lines):
            ax.plot([p[0] for p in line.coords],
                    [p[1] for p in line.coords],
                    color=colors[i])
        return ax

    @staticmethod
    def draw_img_with_a_single_line(title, lst, image, color, is_save: bool = False):
        fig = plt.gcf()
        plt.title(title)
        plt.imshow(image, cmap="gray")
        for p in lst:
            plt.plot(p[0], p[1], '.', c=color)
        plt.gca().set_aspect('auto')
        plt.show()
        if is_save:
            fig.savefig(f'{title}.png', bbox_inches="tight")

    def draw_searching(self, invalid_lines, valid_lines, image):
        for id, lines in enumerate([invalid_lines, valid_lines]):
            title = "valid" if id > 0 else "invalid"
            color = "blue" if id > 0 else "red"
            for viz in lines:
                i, lst = viz["i"], viz["lst"]
                self.draw_img_with_a_single_line(
                    title=f'{i} {title}',
                    lst=lst,
                    image=image,
                    color=color,
                    is_save=True)

    def draw_img_with_roi(self, ax, title):
        ax.title.set_text(title)
        xs, ys = self.road.poly.exterior.xy
        ax.imshow(self.image, cmap='gray')
        ax.plot(xs, ys, c="red")
        return ax

    def draw_img_with_left_right_boundary(self, ax, title):
        ax.title.set_text(title)
        ax.imshow(self.image, cmap="gray")
        boundaries = [list(self.road.left_boundary.coords), list(self.road.right_boundary.coords)]
        for i, coords in enumerate(boundaries):
            color = "blue" if i == 0 else "green"
            ax.plot([p[0] for p in coords],
                    [p[1] for p in coords],
                    color=color)
        return ax

    @staticmethod
    def draw_img(ax, masked_img, title):
        ax.title.set_text(title)
        ax.imshow(masked_img, cmap='gray')
        return ax

    @staticmethod
    def draw_histogram(ax, rotated_img, title, show_peaks: bool = False):
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

        ax.title.set_text(title)
        ax.plot([i for i in range(0, len(hist))], hist)

        if show_peaks:
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
            for peak in peaks:
                ax.plot(peak, hist[peak], '.', color="red")
        return ax
