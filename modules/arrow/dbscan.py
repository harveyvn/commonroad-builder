import cv2
import numpy as np
import matplotlib.pyplot as plt
from typing import List
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

    def find_group_contain_point(self, point, debug: bool = False, img: np.array = None):
        X, labels, group = np.array(self.points), self.db.labels_, []
        target = list(point)
        print(target)
        for i in set(labels):
            Xs = [x.tolist() for x in X[self.db.labels_ == i]]
            print(Xs)
            if target in Xs:
                group = Xs
                break
        if debug:
            plt.title("Found a group contain point: ")
            plt.imshow(img, cmap='gray')
            for c in group:
                plt.scatter(x=c[0], y=c[1], s=1, color='r')
            plt.show()

            for c in group:
                cv2.circle(img, c, radius=3, color=(0, 0, 255), thickness=-1)
            cv2.imshow("Image", img)
            cv2.waitKey(0)
            exit()
        return group

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


