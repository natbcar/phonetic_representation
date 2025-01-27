#!/usr/bin/env python3

import panphon2
import numpy as np
import multiprocess as mp
from sklearn.metrics.pairwise import cosine_distances, euclidean_distances
from scipy.stats import pearsonr, spearmanr
import argparse
from main.utils import load_embd_data, load_multi_data
import collections
import tqdm
import random


def evaluate_correlations(data_multi, data_embd, data_size=1000, jobs=20):
    data_langs = collections.defaultdict(list)

    for (token_ort, token_ipa, lang, pronunciation), emdb in zip(data_multi, data_embd):
        data_langs[lang].append((token_ipa, emdb))

    def compute_panphon_distance(y, data):
        fed = panphon2.FeatureTable().feature_edit_distance
        return [fed(w, y) for w, _ in data]

    corr_pearson_l2_all = {}
    corr_spearman_l2_all = {}
    corr_pearson_cos_all = {}
    corr_spearman_cos_all = {}

    for lang, data in tqdm.tqdm(data_langs.items()):
        # Take only dev data
        r = random.Random(0)
        data = r.sample(data, k=data_size)

        with mp.Pool(jobs) as pool:
            data_dists_fed = np.array(pool.map(
                lambda y: compute_panphon_distance(y[0], data),
                data
            ))

        data_dists_l2 = euclidean_distances(np.array([x[1] for x in data]))
        data_dists_cos = cosine_distances(np.array([x[1] for x in data]))

        corr_pearson_l2 = []
        corr_spearman_l2 = []
        corr_pearson_cos = []
        corr_spearman_cos = []

        for dist_fed, dist_l2, dist_cos in zip(data_dists_fed, data_dists_l2, data_dists_cos):
            corr_pearson_l2.append(pearsonr(dist_fed, dist_l2)[0])
            corr_spearman_l2.append(spearmanr(dist_fed, dist_l2)[0])

            corr_pearson_cos.append(pearsonr(dist_fed, dist_cos)[0])
            corr_spearman_cos.append(spearmanr(dist_fed, dist_cos)[0])

        corr_pearson_l2_all[lang] = abs(np.average(corr_pearson_l2))
        corr_pearson_cos_all[lang] = abs(np.average(corr_pearson_cos))
        corr_spearman_l2_all[lang] = abs(np.average(corr_spearman_l2))
        corr_spearman_cos_all[lang] = abs(np.average(corr_spearman_cos))


    corr_pearson_l2_all["all"] = np.average(list(corr_pearson_l2_all.values()))
    corr_pearson_cos_all["all"] = np.average(list(corr_pearson_cos_all.values()))
    corr_spearman_l2_all["all"] = np.average(list(corr_spearman_l2_all.values()))
    corr_spearman_cos_all["all"] = np.average(list(corr_spearman_cos_all.values()))


    return {
        "pearson L2": corr_pearson_l2_all, "pearson cos": corr_pearson_cos_all,
        "spearman L2": corr_spearman_l2_all, "spearman cos": corr_spearman_cos_all,
    }

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("-d", "--data-multi", default="data/multi.tsv")
    args.add_argument("-e", "--embd", default="computed/embd_bpemb.pkl")
    args = args.parse_args()

    data_multi = load_multi_data(args.data_multi)
    data_embd = load_embd_data(args.embd)

    assert len(data_multi) == len(data_embd)

    output = evaluate_correlations(data_multi, data_embd)
    print("Overall:")
    for key in output:
        print(f"{key}: {output[key]['all']:.2f}")
