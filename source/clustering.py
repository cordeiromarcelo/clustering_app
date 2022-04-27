import numpy as np
import pandas as pd

import scipy.spatial
from haversine import haversine


# Calculate the harversine distance
def distance(p1, p2):
    return haversine(p1[1:], p2[1:])


# Calculate the new centroid of the clusters in each call, with weights
def cluster_centroids(data, clusters, k):
    results = []
    for i in range(k):
        results.append(
            np.average(data[clusters == i], weights=np.squeeze(np.asarray(data[clusters == i][:, [0]])), axis=0))
    return results


# Non conventional kmeans implementation
def kmeans(data, k=None, centroids=None, steps=30):
    # Forgy initialization method: choose k data points randomly.
    centroids = data[np.random.choice(np.arange(len(data)), k, False)]
    elbow = []
    for _ in range(max(steps, 1)):
        sqdists = scipy.spatial.distance.cdist(centroids, data, lambda u, v: (distance(u, v) ** 2))
        elbow.append(sqdists)

        # Index of the closest centroid to each data point.
        clusters = np.argmin(sqdists, axis=0)
        new_centroids = cluster_centroids(data, clusters, k)
        if np.array_equal(new_centroids, centroids):
            break
        centroids = new_centroids

    return clusters, centroids, elbow


def create_clusters(df, lat_col, long_col, peso_col):
    # Create Clusters
    k = 5
    vals = df[[peso_col, lat_col, long_col]].values

    clusters, centroids, elbow = kmeans(vals, k)

    # Get the lat and long from the cluster centroids
    lats = [centroids[i][1] for i in range(k)]
    longs = [centroids[i][2] for i in range(k)]

    # Put the results into the dataset
    df['cluster'] = clusters
    df['cluster_lat'] = df['cluster'].map(lambda x: lats[x])
    df['cluster_lng'] = df['cluster'].map(lambda x: longs[x])

    return df
