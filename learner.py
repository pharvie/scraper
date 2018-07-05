import requester
import fixer
import tensorflow as tf
import os
import pandas as pd
import re
import codecs
from collections import OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import gatherer
from tabulate import tabulate


def learn(root):
    tops = ['default']
    vocab = gatherer.vocab(root)

    def load_directory_data(directory):
        data = OrderedDict([('url', []), ('top', []), ('url_length', []), ('path_length', []), ('purity', []),
                            ('queries', []), ('phrases', []), ('last_path_length', []), ('average_subpath_length', []),
                            ('siblings', []), ('parents', [])])
        for file_path in os.listdir(directory):
            with codecs.open(os.path.join(directory, file_path), "r", encoding='latin-1') as f:
                lines = f.readlines()
                url = lines[0].strip()
                parents = 0
                siblings = 0
                if len(lines) > 1:
                    parents = int(re.search(r'(\d+)', lines[1].strip()).group(1))
                    siblings = int(re.search(r'(\d+)', lines[2].strip()).group(1))
                domain, top = fixer.remove_top(url)
                if top not in tops and not re.search(r'^\d$', top):
                    tops.append(top)
                subpaths = requester.subpaths(url)
                data["url"].append(url)
                data["top"].append(top)
                data['url_length'].append(len(url))
                data['path_length'].append(len(subpaths))
                data['purity'].append(requester.purity(subpaths))
                data['queries'].append(requester.queries(url))
                data['phrases'].append(' '.join(requester.phrases(url)))
                if subpaths:
                    data['last_path_length'].append(len(subpaths[-1]))
                else:
                    data['last_path_length'].append(0)
                average = 0
                for subpath in subpaths:
                    average += len(subpath)/len(subpaths)
                data['average_subpath_length'].append(average)
                data['parents'].append(parents)
                data['siblings'].append(siblings)

        df = pd.DataFrame.from_dict(data)
        print(directory)
        print(tabulate(df, headers=data.keys()))
        return df

    # Merge positive and negative examples, add a polarity column and shuffle.
    def load_dataset(directory):
        pos_df = load_directory_data(os.path.join(directory, "pos"))
        neg_df = load_directory_data(os.path.join(directory, "neg"))
        pos_df["polarity"] = 1
        neg_df["polarity"] = 0
        return pd.concat([pos_df, neg_df]).sample(frac=1).reset_index(drop=True)

    # Download and process the dataset files.
    def download_and_load_datasets(dataset):
        trdf = load_dataset(os.path.join(dataset, "train"))
        tdf = load_dataset(os.path.join(dataset, "test"))
        return trdf, tdf

    train_df, test_df = download_and_load_datasets(root)

    tf.logging.set_verbosity(tf.logging.ERROR)

    train_df.head()

    # Training input on the whole training set with no limit on training epochs.
    train_input_fn = tf.estimator.inputs.pandas_input_fn(
        train_df, train_df["polarity"], num_epochs=None, shuffle=True)

    # Prediction on the whole training set.
    predict_train_input_fn = tf.estimator.inputs.pandas_input_fn(
        train_df, train_df["polarity"], shuffle=False)
    # Prediction on the test set.
    predict_test_input_fn = tf.estimator.inputs.pandas_input_fn(
        test_df, test_df["polarity"], shuffle=False)

    queries_numeric_column = tf.feature_column.numeric_column(key='queries')

    url_numeric_feature_column = tf.feature_column.numeric_column('url_length')

    url_length_feature_column = tf.feature_column.bucketized_column(
        source_column=url_numeric_feature_column,
        boundaries=[0, 10, 20, 30, 40, 50, 70, 90, 120, 160, 200, 300, 400])

    path_numeric_feature_column = tf.feature_column.numeric_column('path_length')

    path_length_feature_column = tf.feature_column.bucketized_column(
        source_column=path_numeric_feature_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    last_path_length_numeric_feature_column = tf.feature_column.numeric_column('last_path_length')

    last_path_length_feature_column = tf.feature_column.bucketized_column(
        source_column=last_path_length_numeric_feature_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    purity_numeric_column = tf.feature_column.numeric_column('purity')

    purity_feature_column = tf.feature_column.bucketized_column(
        source_column=purity_numeric_column,
        boundaries=[-1, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    average_subpath_length_numeric_column = tf.feature_column.numeric_column('average_subpath_length')

    average_subpath_length_column = tf.feature_column.bucketized_column(
        source_column=average_subpath_length_numeric_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100])

    parents_numeric_column = tf.feature_column.numeric_column('parents')

    parents_column = tf.feature_column.bucketized_column(
        source_column=parents_numeric_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
    )

    siblings_numeric_column = tf.feature_column.numeric_column('siblings')

    siblings_column = tf.feature_column.bucketized_column(
        source_column=siblings_numeric_column,
        boundaries=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 140,
                    160, 180, 200, 220, 240, 260, 280, 300, 340, 380, 420, 440, 500]
    )

    top_feature_column = tf.feature_column.categorical_column_with_vocabulary_list(
        key='top',
        vocabulary_list=tops)

    vocab_feature_column = tf.feature_column.categorical_column_with_vocabulary_list(
        key='phrases',
        vocabulary_list=vocab)

    features = [queries_numeric_column,
                tf.feature_column.indicator_column(url_length_feature_column),
                tf.feature_column.indicator_column(path_length_feature_column),
                tf.feature_column.indicator_column(last_path_length_feature_column),
                tf.feature_column.indicator_column(purity_feature_column),
                tf.feature_column.indicator_column(average_subpath_length_column),
                tf.feature_column.indicator_column(parents_column),
                tf.feature_column.indicator_column(siblings_column),
                tf.feature_column.indicator_column(top_feature_column),
                tf.feature_column.indicator_column(vocab_feature_column)]

    # Reduce logging output.
    estimator = tf.estimator.DNNClassifier(
        hidden_units=[500, 100],
        feature_columns=features,
        optimizer=tf.train.AdagradOptimizer(learning_rate=0.003))

    # Training for 1,000 steps means 128,000 training examples with the default
    # batch size. This is roughly equivalent to 5 epochs since the training dataset
    # contains 25,000 examples.
    estimator.train(input_fn=train_input_fn, steps=1000)

    train_eval_result = estimator.evaluate(input_fn=predict_train_input_fn)
    test_eval_result = estimator.evaluate(input_fn=predict_test_input_fn)

    print("Training set accuracy: {accuracy}".format(**train_eval_result))
    print("Test set accuracy: {accuracy}".format(**test_eval_result))
    print("Accuracy baseline: %s" % estimator.evaluate(input_fn=predict_test_input_fn)["accuracy_baseline"])

    def serving_input_fn():
        feature_placeholders = {
            'url': tf.placeholder(tf.string, [None]),
            'top': tf.placeholder(tf.string, [None]),
            'url_length': tf.placeholder(tf.float32, [None]),
            'path_length': tf.placeholder(tf.float32, [None]),
            'purity': tf.placeholder(tf.float32, [None]),
            'queries': tf.placeholder(tf.float32, [None]),
            'last_path_length': tf.placeholder(tf.float32, [None]),
            'average_subpath_length': tf.placeholder(tf.float32, [None]),
            'parents': tf.placeholder(tf.float32, [None]),
            'siblings': tf.placeholder(tf.float32, [None]),
            'phrases': tf.placeholder(tf.string, [None])
        }
        features = {
            key: tf.expand_dims(tensor, -1)
            for key, tensor in feature_placeholders.items()
        }
        return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

    estimator.export_savedmodel(
        root,
        serving_input_fn
    )

    def get_predictions(est, input_fn):
        return [x["class_ids"][0] for x in est.predict(input_fn=input_fn)]

    labels = ["negative", "positive"]

    # Create a confusion matrix on training data.
    with tf.Graph().as_default():
        cm = tf.confusion_matrix(train_df["polarity"],
                                 get_predictions(estimator, predict_train_input_fn))
        with tf.Session() as session:
            cm_out = session.run(cm)

    # Normalize the confusion matrix so that each row sums to 1.
    cm_out = cm_out.astype(float) / cm_out.sum(axis=1)[:, np.newaxis]

    sns.heatmap(cm_out, annot=True, xticklabels=labels, yticklabels=labels)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.interactive(False)
    plt.plot()
    plt.show()


learn('C:\\Users\\pharvie\\Desktop\\Training\\freshiptv')
