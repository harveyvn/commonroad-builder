import numpy as np
import matplotlib.pyplot as plt
from modules.common import pairs, angle
from typing import List, Tuple
from shapely.geometry import Point, LineString
from .contour import Contour


class ArrowLib:
    @staticmethod
    def draw(title, img):
        plt.title(title)
        plt.imshow(img, cmap='gray')
        plt.show()

    @staticmethod
    def get_centeroid(cnt):
        length = len(cnt)
        sum_x = np.sum(cnt[..., 0])
        sum_y = np.sum(cnt[..., 1])
        return int(sum_x / length), int(sum_y / length)

    @staticmethod
    def contour2list(contours):
        return np.vstack(contours).squeeze()

    @staticmethod
    def get_sorted_contours_by_length(contours: List[Contour]):
        return sorted(contours, key=lambda x: x.length)

    @staticmethod
    def find_contours_by_centroid(targets: List[Tuple], contours: List[Contour],
                                  debug: bool = False, img: np.array = None):
        result = []
        for c in contours:
            for t in targets:
                if t == c.centeroid:
                    result.append(c)

        if debug:
            fig, ax = plt.subplots(1, 2, figsize=(16, 8))
            ax[0].title.set_text("Contours before filter")
            ax[0].imshow(img, cmap='gray')
            for c in contours:
                v = c.centeroid
                ax[0].scatter(x=v[0], y=v[1], s=5, color='b')

            ax[1].title.set_text("Contours after filter")
            ax[1].imshow(img, cmap='gray')
            for c in result:
                v = c.centeroid
                ax[1].scatter(x=v[0], y=v[1], s=5, color='r')
            plt.show()
            exit()

        return result

    @staticmethod
    def find_shortest_pair(contours: List[Contour], debug: bool = False, img: np.array = None):
        pair: List[Contour] = []
        min_distance = 1000000
        for c1, c2 in pairs(contours):
            p1 = Point(c1.centeroid)
            p2 = Point(c2.centeroid)
            mdis = p1.distance(p2)
            if mdis < min_distance:
                min_distance = mdis
                pair = [c1, c2]

        if debug:
            fig, ax = plt.subplots(1, 2, figsize=(16, 8))
            ax[0].title.set_text("Shortest pair")
            ax[0].imshow(img, cmap='gray')
            for c in pair:
                v = c.centeroid
                ax[0].scatter(x=v[0], y=v[1], s=5, color='b')

            ax[1].title.set_text("Arrow boundary")
            ax[1].imshow(img, cmap='gray')
            for c in pair:
                ps = np.vstack(c.coords).squeeze()
                for p in ps:
                    ax[1].scatter(p[0], p[1], s=1, color='r')
            plt.show()
            exit()

        return pair

    @staticmethod
    def find_deg_of(c1: Contour, c2: Contour, debug: bool = False):
        point_line, point_tria = None, None
        for c in [c1, c2]:
            if c.type == "triangle":
                point_tria = c.centeroid
            else:
                point_line = c.centeroid

        lst = LineString([point_line, point_tria])
        lineA, lineB = list(lst.coords), [[0, 0], [1, 0]]
        diff = angle(lineA, lineB)
        cm = None
        if 0 <= diff < 10:
            cm = "0 deg Ox - right"
        if 170 < diff <= 180:
            cm = "180 deg Ox - left"
        if 85 <= diff <= 90:
            lineA, lineB = list(lst.coords), [[0, 0], [0, 1]]
            diff = angle(lineA, lineB)
            if 0 <= diff < 10:
                cm = "0 deg Oy - down"
            if 170 < diff <= 180:
                cm = "180 deg Oy - up"

        if cm is None:
            cm = f'deg Ox'

        if debug:
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            x1, y1 = point_line[0], point_line[1]
            x2, y2 = point_tria[0], point_tria[1]
            ax.title.set_text(str(diff) + ' ' + cm)
            ax.plot((x1, x2), (y1, y2), c="black")
            ax.plot(point_line[0], point_line[1], marker='.', c='b')
            ax.plot(point_tria[0], point_tria[1], marker='.', c='r')
            ax.annotate("", xy=(x2+0.1, y2+0.1), xytext=(x2, y2), arrowprops=dict(arrowstyle="->"))
            plt.show()
            exit()

        return diff, cm
