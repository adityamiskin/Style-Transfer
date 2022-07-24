from flask import Flask, render_template, request, jsonify

import os
import tensorflow as tf

os.environ["TFHUB_MODEL_LOAD_FORMAT"] = "COMPRESSED"

import numpy as np
import PIL.Image
import cv2
import glob
import tensorflow_hub as hub

import json
import base64
from io import BytesIO


style_predict_path = tf.keras.utils.get_file(
    "style_predict.tflite",
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/prediction/1?lite-format=tflite",
)
style_transform_path = tf.keras.utils.get_file(
    "style_transform.tflite",
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/transfer/1?lite-format=tflite",
)


def tensor_to_image(tensor):
    tensor = tensor * 255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return PIL.Image.fromarray(tensor)


def load_img(path_to_img):
    max_dim = 512
    img = tf.io.read_file(path_to_img)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)

    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim

    new_shape = tf.cast(shape * scale, tf.int32)

    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img


def convert_to_img(base_string, fileName):
    imgdata = base64.b64decode(base_string)
    filename = fileName
    with open(filename, "wb") as f:
        f.write(imgdata)
    return filename


def preprocess_image(image, target_dim):
    # Resize the image so that the shorter dimension becomes 256px.
    shape = tf.cast(tf.shape(image)[1:-1], tf.float32)
    short_dim = min(shape)
    scale = target_dim / short_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    image = tf.image.resize(image, new_shape)

    # Central crop the image.
    image = tf.image.resize_with_crop_or_pad(image, target_dim, target_dim)

    return image


def run_style_predict(preprocessed_style_image):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_predict_path)

    # Set model input.
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    interpreter.set_tensor(input_details[0]["index"], preprocessed_style_image)

    # Calculate style bottleneck.
    interpreter.invoke()
    style_bottleneck = interpreter.tensor(
        interpreter.get_output_details()[0]["index"]
    )()

    return style_bottleneck


# Run style transform on preprocessed style image
def run_style_transform(style_bottleneck, preprocessed_content_image):
    # Load the model.
    interpreter = tf.lite.Interpreter(model_path=style_transform_path)

    # Set model input.
    input_details = interpreter.get_input_details()
    interpreter.allocate_tensors()

    # Set model inputs.
    interpreter.set_tensor(input_details[0]["index"], preprocessed_content_image)
    interpreter.set_tensor(input_details[1]["index"], style_bottleneck)
    interpreter.invoke()

    # Transform content image.
    stylized_image = interpreter.tensor(interpreter.get_output_details()[0]["index"])()

    return stylized_image


def processing(output):

    _, style = output[0]["style"].split(",")
    _, content = output[1]["target"].split(",")

    style = convert_to_img(style, "style.jpg")
    content = convert_to_img(content, "content.jpg")

    style_image = load_img(style)
    content_image = load_img(content)

    style_image = preprocess_image(style_image, 256)
    content_image = preprocess_image(content_image, 384)

    style_bottleneck = run_style_predict(style_image)
    stylized_image = run_style_transform(style_bottleneck, content_image)

    if len(stylized_image.shape) > 3:
        stylized_image = tf.squeeze(stylized_image, axis=0)

    result = tensor_to_image(stylized_image)

    buff = BytesIO()
    result.save(buff, format="JPEG")
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")

    return new_image_string


app = Flask(
    __name__,
    static_url_path="",
    static_folder="web/static",
    template_folder="web/templates",
)


@app.route("/", methods=["GET", "POST"])
def root():
    """Return the home page."""
    global output
    if request.method == "POST":
        output = request.get_json()
        final_ouput = processing(output)
        return jsonify(final_ouput)
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
