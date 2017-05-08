# Load pickled data
import os
import helpers
import architecture
import pickle
import tensorflow as tf
import cv2
import sklearn as skl
import numpy as np

# Load preprocessed data
training_file = 'train_preproc_data.p'
validation_file = 'valid_preproc_data.p'
testing_file = 'test_preproc_data.p'
if not os.path.isfile(training_file) or not os.path.isfile(validation_file) or not os.path.isfile(testing_file):
    print("ERROR: Run preproc.py to create ", " ", training_file, " ", validation_file, " ", testing_file)
else:
    with open(training_file, mode='rb') as f:
        train = pickle.load(f)
    with open(validation_file, mode='rb') as f:
        valid = pickle.load(f)
    with open(testing_file, mode='rb') as f:
        test = pickle.load(f)
    X_train, y_train = train['features'], train['labels']
    X_valid, y_valid = valid['features'], valid['labels']
    X_test, y_test = test['features'], test['labels']

    # Hyperparameters
    EPOCHS = 15
    BATCH_SIZE = 128
    rate = 0.0002
    dropout = 0.50

    # Set up TensorFlow input and output
    x = tf.placeholder(tf.float32, (None, 32, 32, 1))  # floats for normalized data
    y = tf.placeholder(tf.int32, (None))
    one_hot_y = tf.one_hot(y, 42)
    keep_prob = tf.placeholder(tf.float32)
    logits, regularizers = architecture.MultiScaleCNNArchV2(x, keep_prob)
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=one_hot_y, logits=logits)
    loss_operation = tf.reduce_mean(cross_entropy) + 1e-5 * regularizers
    optimizer = tf.train.AdamOptimizer(learning_rate=rate)
    training_operation = optimizer.minimize(loss_operation)
    # model evaluation
    correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(one_hot_y, 1))
    accuracy_operation = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    saver = tf.train.Saver()

    # training
    max_accuracy = 0
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        num_examples = X_train.shape[0]

        print("Training with batch size ", BATCH_SIZE)
        print()
        for i in range(EPOCHS):
            X_train, y_train = skl.utils.shuffle(X_train, y_train)
            # process each batch
            for offset in range(0, num_examples, BATCH_SIZE):
                end = offset + BATCH_SIZE
                batch_x, batch_y = X_train[offset:end], y_train[offset:end]
                _, loss = sess.run([training_operation, loss_operation], feed_dict={x: batch_x, y: batch_y, keep_prob: dropout})  # execute session
            validation_accuracy = helpers.evaluate(X_valid, y_valid, accuracy_operation, BATCH_SIZE, x, y, keep_prob)
            print("EPOCH {} ...".format(i + 1), " validation accuracy = {:.3f}".format(validation_accuracy))
            if validation_accuracy > max_accuracy:  # save only highest accuracy we've achieved so far
                max_accuracy = validation_accuracy
                saver.save(sess, './best_model_save_file')
                print("Highest accuracy seen so far. Model saved.")
            else:
                print("Not highest accuracy seen so far. Model not saved.")
            print()
