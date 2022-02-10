import numpy as np
import matplotlib.pyplot as plt
from modules.common import pairs
from typing import List, Tuple
from shapely.geometry import Point
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
            ax[0].title.set_text("Before filter")
            ax[0].imshow(img, cmap='gray')
            for c in contours:
                v = c.centeroid
                ax[0].scatter(x=v[0], y=v[1], s=5, color='b')

            ax[1].title.set_text("After filter")
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
            print(p1, p2, mdis)
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
                    print(p, (p[0], p[1]))
                    ax[1].scatter(p[0], p[1], s=1, color='r')
            plt.show()
            exit()

        return pair
