"""Flask app for pixly app."""

import os
from flask import Flask, render_template, request, redirect
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
import boto3
import uuid
from exif import Image

load_dotenv()

app = Flask(__name__)

app.config['S3_BUCKET'] = os.environ["S3_BUCKET_NAME"]
app.config['S3_KEY'] = os.environ["AWS_ACCESS_KEY"]
app.config['S3_SECRET'] = os.environ["AWS_ACCESS_SECRET"]
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

s3 = boto3.client(
    "s3",
    "us-west-1",
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET']
)

toolbar = DebugToolbarExtension(app)

@app.get("/")
def get_images():
    return render_template("form.html")


def make_unique_filename():
    new_filename = uuid.uuid4().hex + ".jpg"
    return new_filename


def get_metadata(image_filename):
    with open(image_filename, "rb") as image_file:
        image_data = Image(image_file)

        toPrint = image_data.list_all()
        print ("Image data:", toPrint)
        print("model", image_data.model)
        print("make", image_data.make)
        print("x_res", image_data.x_resolution)
        print("pixel_x_dim", image_data.pixel_x_dimension)



def send_file_to_s3(file, bucket):
    try:
        print("filename=", file.filename)

        s3.upload_file(file.filename, bucket, file.filename)
    except Exception as e:
        return f"Error occurred: {e}"

    return "file successfully uploaded"

@app.post("/")
def add_image():
    image = request.files["file"]
    print("image=", image)

    if image.filename != "":
        image.filename = make_unique_filename()
        image.save(image.filename)
        result = send_file_to_s3(image, app.config['S3_BUCKET'])
        get_metadata(image.filename)
        os.remove(image.filename)
        return result
    else:
        print("no image grabbed from file upload")

