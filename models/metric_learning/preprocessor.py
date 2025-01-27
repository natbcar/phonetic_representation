import panphon, panphon2
from main.utils import load_multi_data

def preprocess_dataset(data, features, lang):
    # token_ort, token_ipa, lang, pronunc
    data = [
        x[:2] for x in load_multi_data(data)
        if lang == "multi" or x[2] == lang
    ]
    if features == "panphon":
        return preprocess_dataset_panphon(data)
    else:
        return preprocess_dataset_token(data, features)


def preprocess_dataset_panphon(data):
    import numpy as np
    f = panphon2.FeatureTable()
    # panphon, token_ipa
    return [(np.array(f.word_to_binary_vectors(x[1])), x[1]) for x in data]


def preprocess_dataset_token(data, features):
    from torchtext.vocab import build_vocab_from_iterator
    import torch
    import torch.nn.functional as F

    # use the same multi vocabulary across all models
    # a nice side effect is the same number of parameters everywhere
    if features == "tokenort":
        vocab_raw = open("data/vocab/ort_multi.txt", "r").read().split("\n")
        vocab = build_vocab_from_iterator([[x] for x in vocab_raw])
    elif features == "tokenipa":
        vocab_raw = open("data/vocab/ipa_multi.txt", "r").read().split("\n")
        vocab = build_vocab_from_iterator([[x] for x in vocab_raw])

    def token_onehot(word):
        return F.one_hot(torch.tensor(vocab(list(word))), num_classes=len(vocab)).float()

    # features, token_ipa
    if features == "tokenort":
        data = [(token_onehot(x[0]), x[1]) for x in data]
    elif features == "tokenipa":
        ft = panphon.FeatureTable()
        data = [(token_onehot(ft.ipa_segs(x[1])), x[1]) for x in data]

    return data
