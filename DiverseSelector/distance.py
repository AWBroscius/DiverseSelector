# -*- coding: utf-8 -*-
# The DiverseSelector library provides a set of tools to select molecule
# subset with maximum molecular diversity.
#
# Copyright (C) 2022 The QC-Devs Community
#
# This file is part of DiverseSelector.
#
# DiverseSelector is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# DiverseSelector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --

"""Metric calculation module."""

from typing import Any

from DiverseSelector.utils import sklearn_supported_metrics
import numpy as np
from scipy.spatial.distance import squareform
from sklearn.metrics import pairwise_distances

__all__ = [
    "compute_distance_matrix",
    "bit_tanimoto",
    "euc_bit",
    "modified_tanimoto",
    "pairwise_similarity_bit",
    "tanimoto",
]


def compute_distance_matrix(
    features: np.ndarray,
    metric: str = "euclidean",
    n_jobs: int = -1,
    force_all_finite: bool = True,
    **kwargs: Any,
):
    """Compute pairwise distance given a feature matrix.

    Parameters
    ----------
    features : np.ndarray
        Molecule feature matrix.
    metric : str, optional
        Distance metric.
    n_jobs : int, optional
        Number of jobs to run in parallel. Default=-1, which means all CPUs.
    force_all_finite : bool, optional
        Whether to raise an error on np.inf and np.nan in X. Default=True.

    Returns
    -------
    dist : ndarray
        Symmetric distance array.
    """
    # todo: add more metrics implemented here
    built_in_metrics = [
        "tanimoto",
        "modified_tanimoto",
    ]

    # Check if specified metric is supported
    if metric in sklearn_supported_metrics:
        dist = pairwise_distances(
            X=features,
            Y=None,
            metric=metric,
            n_jobs=n_jobs,
            force_all_finite=force_all_finite,
            **kwargs,
        )
    elif metric in built_in_metrics:
        function_dict = {
            "tanimoto": tanimoto,
            "modified_tanimoto": modified_tanimoto,
        }

        dist = function_dict[metric](features)
    else: # raise error if unsupported
        raise ValueError(f"Metric {metric} is not supported by the library.")

    return dist


def pairwise_similarity_bit(feature: np.array, metric: str) -> np.ndarray:
    """Compute the pairwise similarity coefficients.

    Parameters
    ----------
    feature : ndarray
        Feature matrix.
    metric : str
        Method of calculation.

    Returns
    -------
    pair_coeff : ndarray
        Similarity coefficients for all molecule pairs in feature matrix.
    """
    pair_simi = []
    size = len(feature)
    for i in range(0, size):
        for j in range(i + 1, size):
            pair_simi.append(metric(feature[i], feature[j]))
    pair_coeff = squareform(pair_simi) + np.identity(size)
    return pair_coeff


def euc_bit(a: np.array, b: np.array) -> float:
    """Compute Euclidean distance from bitstring.

    Parameters
    ----------
    a : array_like
        molecule A's features in bits.
    b : array_like
        molecules B's features in bits.

    Returns
    -------
    euc_dist : float
        Euclidean distance between molecules A and B.

    Notes
    -----
    euclidean_dist = sqrt(a^2 + b^2 - 2*(a&b))

    Bajusz, D., Rácz, A., and Héberger, K.. (2015)
    Why is Tanimoto index an appropriate choice for fingerprint-based similarity calculations?.
    Journal of Cheminformatics 7.
    """
    # Count non-trivial features in a and b
    a_feat = np.count_nonzero(a)
    b_feat = np.count_nonzero(b)
    # compute intersection of a and b
    c = 0
    for idx, _ in enumerate(a):
        if a[idx] == b[idx] and a[idx] != 0:
            c += 1
    # compute euclidean distance
    euc_dist = (a_feat + b_feat - (2 * c)) ** 0.5
    return euc_dist


def tanimoto(a: np.array, b: np.array) -> float:
    """Compute Tanimoto coefficient.

    Parameters
    ----------
    a : array_like
        Molecule A's features.
    b : array_like
        Molecules B's features.

    Returns
    -------
    coeff : float
        Tanimoto coefficient for molecules A and B.

    Notes
    -----
    The Tanimoto coefficient computes similarity by taking the intersection of A and B over their union.
    T(A,B) = (A & B) / A + B - (A & B)

    Bajusz, D., Rácz, A., and Héberger, K.. (2015)
    Why is Tanimoto index an appropriate choice for fingerprint-based similarity calculations?.
    Journal of Cheminformatics 7.
    """
    coeff = (sum(a * b)) / ((sum(a ** 2)) + (sum(b ** 2)) - (sum(a * b)))
    return coeff


def bit_tanimoto(a: np.array, b: np.array) -> float:
    """Compute Tanimoto coefficient for molecules A and B, with features in bitstring form.

    Parameters
    ----------
    a : array_like
        Molecule A's features in bitstring.
    b : array_like
        Molecules B's features in bitstring.

    Returns
    -------
    coeff : float
        Tanimoto coefficient for molecules A and B.

    Notes
    -----
    The Tanimoto coefficient computes similarity by taking the intersection of A and B over their union.
    T(A,B) = (A & B) / A + B - (A & B)

    Bajusz, D., Rácz, A., and Héberger, K.. (2015)
    Why is Tanimoto index an appropriate choice for fingerprint-based similarity calculations?.
    Journal of Cheminformatics 7.
    """
    a_feat = np.count_nonzero(a)
    b_feat = np.count_nonzero(b)
    # compute intersection of a and b
    c = 0
    for idx, _ in enumerate(a):
        if a[idx] == b[idx] and a[idx] != 0:
            c += 1
    # compute bitwise tanimoto
    bit_tani = c / (a_feat + b_feat - c)
    return bit_tani


def modified_tanimoto(a: np.array, b: np.array) -> float:
    """Compute the modified tanimoto coefficient from bitstrings of molecules A and B.

    Parameters
    ----------
    a : array_like
        Molecule A's features in bitstring.
    b : array_like
        Molecules B's features in bitstring.

    Returns
    -------
    mt : float
        Modified tanimoto coefficient for molecule A and B.

    Notes
    -----
    Adjusts calculation of the Tanimoto coefficient to counter its natural bias towards
    smaller molecules using a Bernoulli probability model.

     mt = (((2 - p) / 3) * t_1) + (((1 + p) / 3) * t_0)
     p = success probability of independent trials
     t_1 = intersection of '1' bits in a and b
     t_0 = intersection of '0' bits in a and b

    Fligner, M. A., Verducci, J. S., and Blower, P. E.. (2002)
    A Modification of the Jaccard-Tanimoto Similarity Index for
    Diverse Selection of Chemical Compounds Using Binary Strings.
    Technometrics 44, 110-119.
    """
    n = len(a)
    # intersection of '1' bits
    n_11 = sum(a * b)
    # intersection of '0' bits
    n_00 = sum((1 - a) * (1 - b))

    # calculate in terms of '1' bits
    if n_00 == n:
        t_1 = 1
    else:
        t_1 = n_11 / (n - n_00)
    # calculate in terms of '0' bits
    if n_11 == n:
        t_0 = 1
    else:
        t_0 = n_00 / (n - n_11)
    # combine into modified tanimoto using Bernoulli Model
    p = ((n - n_00) + n_11) / (2 * n)
    mt = (((2 - p) / 3) * t_1) + (((1 + p) / 3) * t_0)
    return mt


def nearest_average_tanimoto(x: np.ndarray) -> float:
    """Computes the average tanimoto for nearest molecules.

    Parameters
    ----------
    x : ndarray
        Feature matrix.

    Returns
    -------
    nat : float
        Average tanimoto of closest pairs.

    Notes
    -----
    This computes the tanimoto coefficient of pairs with the shortest
    distances, then returns the average of them.
    This calculation is explictly for the explicit diversity index.

    Papp, Á., Gulyás-Forró, A., Gulyás, Z., Dormán, G., Ürge, L.,
    and Darvas, F.. (2006) Explicit Diversity Index (EDI):
    A Novel Measure for Assessing the Diversity of Compound Databases.
    Journal of Chemical Information and Modeling 46, 1898-1904.
    """
    tani = []
    for idx, _ in enumerate(x):
        short = 100  # arbitary distance
        a = 0
        b = 0
        for jdx, _ in enumerate(x):  # search for shortest distance
            if euc_bit(x[idx], x[jdx]) < short and idx != jdx:
                short = euc_bit(x[idx], x[jdx])
                a = idx
                b = jdx
        # calculate tanimoto for each shortest dist pair
        tani.append(bit_tanimoto(x[a], x[b]))
    # compute average of all shortest tanimoto coeffs
    nat = np.average(tani)
    return nat
