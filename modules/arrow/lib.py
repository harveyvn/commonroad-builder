import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
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
