import matplotlib.pyplot as plt
import numpy as np
from typing import List
from sklearn.cluster import DBSCAN
from .contour import Contour


class ArrowLib:
    @staticmethod
    def group_by_dbscan(centers: List, epsilon=45, min_samples=3, debug: bool = False, img: np.array = None):
        X = np.array(centers)
        db = DBSCAN(eps=epsilon, min_samples=min_samples).fit(X)
        # Number of clusters in labels, ignoring noise if present.
        labels = db.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        if debug:
            y_pred = db.fit_predict(X)
            fig, ax = plt.subplots(1, 2, figsize=(16, 8))
            ax[0].title.set_text("Clusters determined by DBSCAN")
            ax[0].imshow(img, cmap='gray')
            ax[0].scatter(X[:, 0], X[:, 1], c=y_pred, cmap='Paired', s=10)

            ax[1].title.set_text("Clusters determined by DBSCAN no image")
            ax[1].scatter(X[:, 0], X[:, 1], c=y_pred, cmap='Paired', s=10)
            plt.show()
            exit()
        pass

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
