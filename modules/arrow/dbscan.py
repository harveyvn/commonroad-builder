import numpy as np
from typing import List
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN


class DBScan:
    def __init__(self, points: List, epsilon=45, min_samples=3):
        X = np.array(points)
        self.points = points
        self.db = DBSCAN(eps=epsilon, min_samples=min_samples).fit(X)

    def get_info(self, debug: bool = False):
        labels = self.db.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)
        if debug:
            print("Labels: ", labels)
            print("Estimated number of clusters: %d" % n_clusters_)
            print("Estimated number of noise points: %d" % n_noise_)
            print("=======")
        return labels, n_clusters_, n_noise_

    def debug(self, img: np.array):
        X = np.array(self.points)
        y_pred = self.db.fit_predict(X)
        fig, ax = plt.subplots(1, 2, figsize=(16, 8))
        ax[0].title.set_text("Clusters determined by DBSCAN")
        ax[0].imshow(img, cmap='gray')
        ax[0].scatter(X[:, 0], X[:, 1], c=y_pred, cmap='Paired', s=10)

        ax[1].title.set_text("Clusters determined by DBSCAN no image")
        ax[1].scatter(X[:, 0], X[:, 1], c=y_pred, cmap='Paired', s=10)
        plt.show()
        exit()


