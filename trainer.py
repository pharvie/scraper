import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import learner

def train(directory):
    # Reduce logging output.
    tf.logging.set_verbosity(tf.logging.ERROR)

    train_df, test_df = learner.download_and_load_datasets(directory)
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

    features = learner.features()

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


    def get_predictions(estimator, input_fn):
        return [x["class_ids"][0] for x in estimator.predict(input_fn=input_fn)]


    LABELS = [
        "negative", "positive"
    ]

    # Create a confusion matrix on training data.
    with tf.Graph().as_default():
        cm = tf.confusion_matrix(train_df["polarity"],
                                 get_predictions(estimator, predict_train_input_fn))
        with tf.Session() as session:
            cm_out = session.run(cm)

    # Normalize the confusion matrix so that each row sums to 1.
    cm_out = cm_out.astype(float) / cm_out.sum(axis=1)[:, np.newaxis]

    sns.heatmap(cm_out, annot=True, xticklabels=LABELS, yticklabels=LABELS)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.interactive(False)
    plt.plot()
    plt.show()


train('C:\\Users\\pharvie\Desktop\BitLearner')