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

    def draw_searching(self, sorted_lines, valid_lines, image, is_save: bool = False):
        for id, lines in enumerate([sorted_lines]):
            title = "invalid"
            color = "red"
            for viz in lines:
                i, lst = viz["i"], viz["lst"]
                self.draw_img_with_a_single_line(
                    title=f'{i}',
                    lst=lst,
                    image=image,
                    color=color,
                    is_save=is_save)

        for id, lines in enumerate([valid_lines]):
            title = "valid"
            color = "blue"
            for viz in lines:
                i, lst = viz["i"], viz["points"]
                self.draw_img_with_a_single_line(
                    title=f'{i}',
                    lst=lst,
                    image=image,
                    color=color,
                    is_save=is_save)

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
        colors = ["blue", "green"]
        for i, coords in enumerate(boundaries):
            ax.plot([p[0] for p in coords],
                    [p[1] for p in coords],
                    color=colors[i])
        return ax

    @staticmethod
    def draw_img(ax, masked_img, title):
        ax.title.set_text(title)
        ax.imshow(masked_img, cmap='gray')
        ax = plt.gca().set_aspect('auto')
        return ax

    @staticmethod
    def draw_img_1(ax, masked_img, title):
        ax.title.set_text(title)
        ax.imshow(masked_img, cmap='gray')
        # p = 200
        # ax.set_ylim([0, p])
        # ax.set_xlim([240, 255])
        return ax

    @staticmethod
    def draw_histogram(ax, rotated_img, xs_dict, peaks, title, show_peaks: bool = False):
        # Find a histogram
        ax.title.set_text(title)
        xs = [i for i in range(0, rotated_img.shape[1])]
        ys = [0 for i in range(0, rotated_img.shape[1])]
        for k in xs_dict:
            ys[k] = xs_dict[k]
        ax.plot(xs, ys)
        ax.plot(peaks, [ys[x] for x in peaks], '.', color="red")

        print(xs_dict)

        peaks_ys = [ys[x] for x in peaks]
        p = max(peaks_ys) + 10
        # ax.plot([-5, 10, 10, -5, -5], [p, p, 0, 0, p], '-', color="orange")
        # ax.plot([120, 135, 135, 120, 120], [p, p, 0, 0, p], '-', color="orange")
        # ax.plot([240, 255, 255, 240, 240], [p, p, 0, 0, p], '-', color="orange")

        # ax.set_ylim([0, max(peaks_ys)+20])
        # ax.set_xlim([240, 255])
        return ax

