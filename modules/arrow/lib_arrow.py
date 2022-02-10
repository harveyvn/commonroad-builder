import matplotlib.pyplot as plt
import numpy as np


def draw(title, img):
    plt.title(title)
    plt.imshow(img, cmap='gray')
    plt.show()


def get_centeroid(cnt):
    length = len(cnt)
    sum_x = np.sum(cnt[..., 0])
    sum_y = np.sum(cnt[..., 1])
    return int(sum_x / length), int(sum_y / length)


def contour2list(contours):
    return np.vstack(contours).squeeze()
