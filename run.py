import matplotlib.pyplot as plt
import numpy as np
import os
import PIL
import tensorflow as tf
import pathlib
import argparse

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

from models.SequentialModel import SequentialModel


# Some Definitions
TRAINING_EPOCHS = 2
BATCH_SIZE = 32
IMG_HEIGHT = 180
IMG_WIDTH = 180
AUTOTUNE = tf.data.AUTOTUNE
MODEL_SAVE_PATH = "./model_save/weights"


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--train", type=int,
                    help="Train the model using N epochs.")
parser.add_argument("-p", "--predict", type=str,
                    help="Predict an image class. -p <IMG_PATH>")
args = parser.parse_args()


def download_dataset():
    dataset_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
    data_dir = tf.keras.utils.get_file('flower_photos', origin=dataset_url, untar=True)
    data_dir = pathlib.Path(data_dir)
    return data_dir


def check_dataset(data_dir):
    print("Checking dataseti size...")
    image_count = len(list(data_dir.glob('*/*.jpg')))
    print("Dataset size: ", image_count)


def create_train_dataset(data_dir):
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=102030,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )
    return train_ds


def create_validation_dataset(data_dir):
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )
    return val_ds


def tune_models(train_ds, val_ds):
    tunned_train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    tunned_val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    return tunned_train_ds, tunned_val_ds


def create_model(num_classes):
    seq_model = SequentialModel()
    seq_model.build(IMG_HEIGHT, IMG_WIDTH, num_classes)
    return seq_model


def train_model(seq_model, train_ds, val_ds):
    epochs = TRAINING_EPOCHS
    history = seq_model.model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs
    )
    return history


def predict_from_file(seq_model, img_filename):
    """
    Load an image and predict using the trained Model.
    Args:
        seq_model: SequentialModel class instance.
        img_filename: name of the img file to be loaded.
    Return: None.
    """

    img = tf.keras.utils.load_img(
        img_filename, target_size=(IMG_HEIGHT, IMG_WIDTH)
    )
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)

    predictions = seq_model.model.predict(img_array)
    score = tf.nn.softmax(predictions[0])

    print(
        "PREDICT: This image most likely belongs to {} with a {:.2f} percent confidence."
        .format(class_names[np.argmax(score)], 100 * np.max(score))
    )


if __name__ == "__main__":

    if args.train:
        TRAINING_EPOCHS = args.train
        print("Starting training...")
        data_dir = download_dataset()
        check_dataset(data_dir)
        train_ds = create_train_dataset(data_dir)
        class_names = train_ds.class_names
        val_ds = create_validation_dataset(data_dir)
        train_ds, val_ds = tune_models(train_ds, val_ds)

        num_classes = len(class_names)

        seq_model = create_model(num_classes)

        history = train_model(seq_model, train_ds, val_ds)
        
        seq_model.save(MODEL_SAVE_PATH) 

        print("Finished training.")

    if args.predict:
        print("Predicting images...")

        # TODO: Loading train_ds just to get number of classes. Need to change that.
        data_dir = download_dataset()
        train_ds = create_train_dataset(data_dir)
        class_names = train_ds.class_names
        num_classes = len(class_names)
        
        seq_model = create_model(num_classes)

        # Load model weights from Tensorflow saving.
        seq_model.load(MODEL_SAVE_PATH)
        
        predict_from_file(seq_model, args.predict) 
        
        print("Finisihed predictions.")
