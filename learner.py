import tensorflow as tf
import numpy as np
import os
import pandas as pd
import requester
from tabulate import tabulate
import re
import codecs
from collections import OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns

domains = []
tops = ['default']


def load_directory_data(directory):
    print(directory)
    data = OrderedDict([('url', []), ('top', []), ('url_length', []), ('path_length', []), ('purity', []), ('params', [])])
    for file_path in os.listdir(directory):
        with codecs.open(os.path.join(directory, file_path), "r", encoding='latin-1') as f:
            url = f.read()
            domain, top = requester.remove_top(url)
            if top not in tops and not re.search(r'^\d$', top):
                tops.append(top)
            subpaths = requester.subpaths(url)
            data["url"].append(url)
            data["top"].append(top)
            data['url_length'].append(len(url))
            data['path_length'].append(len(subpaths))
            data['purity'].append(requester.purity(subpaths))
            data['params'].append(requester.params(url))

    df = pd.DataFrame.from_dict(data)
    print(tops)
    return df

def features():
    url_numeric_feature_column = tf.feature_column.numeric_column('url_length')
    path_numeric_feature_column = tf.feature_column.numeric_column('path_length')
    purity_numeric_column = tf.feature_column.numeric_column('purity')
    params_numeric_column = tf.feature_column.numeric_column(key='params')

    url_length_feature_column = tf.feature_column.bucketized_column(
        source_column=url_numeric_feature_column,
        boundaries=[0, 10, 20, 30, 40, 50, 70, 90, 120, 160, 200, 300, 400])

    path_length_feature_column = tf.feature_column.bucketized_column(
        source_column=path_numeric_feature_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    purity_feature_column = tf.feature_column.bucketized_column(
        source_column=purity_numeric_column,
        boundaries=[-1, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    tops_feature_column = tf.feature_column.categorical_column_with_vocabulary_list(
        key='top',
        vocabulary_list=tops, default_value=0)

    return [tf.feature_column.indicator_column(url_length_feature_column), tf.feature_column.indicator_column(tops_feature_column),
        tf.feature_column.indicator_column(path_length_feature_column), tf.feature_column.indicator_column(purity_feature_column),
        params_numeric_column]


# Merge positive and negative examples, add a polarity column and shuffle.
def load_dataset(directory):
    pos_df = load_directory_data(os.path.join(directory, "pos"))
    neg_df = load_directory_data(os.path.join(directory, "neg"))
    pos_df["polarity"] = 1
    neg_df["polarity"] = 0
    return pd.concat([pos_df, neg_df]).sample(frac=1).reset_index(drop=True)


# Download and process the dataset files.
def download_and_load_datasets(dataset):
    train_df = load_dataset(os.path.join(dataset, "train"))
    test_df = load_dataset(os.path.join(dataset, "test"))
    return train_df, test_df