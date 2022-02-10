import matplotlib.pyplot as plt
import numpy as np
from typing import List
from .contour import Contour


class Arrow:
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
