"""Flask app for pixly app."""
import os
from flask import Flask, render_template, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
from model import connect_db, db, Photo
from flask_cors import CORS

load_dotenv()

from utilities import make_unique_filename, get_image_metadata, send_file_to_s3


app = Flask(__name__)
CORS(app)

app.config['S3_BUCKET'] = os.environ["S3_BUCKET_NAME"]
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['S3_KEY'] = os.environ["AWS_ACCESS_KEY"]
app.config['S3_SECRET'] = os.environ["AWS_ACCESS_SECRET"]

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "postgresql:///photos")

toolbar = DebugToolbarExtension(app)

connect_db(app)


@app.get("/")
def get_all_photos():
    """Displays page with all photos"""

    camera = request.args.get("camera")
    location = request.args.get("location")


    photos = []
    if camera:
        photos = Photo.camera.ilike(f"%{camera}%")

    elif location:
        photos = Photo.location.ilike(f"%{location}%")

    else:
        photos = Photo.query.all()

    serialized = [photo.serialize() for photo in photos]

    jsonified = jsonify(photos=serialized)
    jsonified.headers.add("Access-Control-Allow-Origin", "*")
    return jsonified


@app.post("/")
def add_image():
    """Grabs a file object of image.  Uses file object to upload image to aws.
    Gets metadata from file object. Saves metadata in database.
    Returns success message with metadata or error message."""
    image = request.files["image"]
    alt = request.form["alt_text"]
    print("alt=", alt)

    if image.filename != "":
        image.filename = make_unique_filename()
        image.save(image.filename)
        send_file_to_s3(image, app.config['S3_BUCKET'])

        image_data = get_image_metadata(image.filename)
        Photo.add_to_db(image_data, alt)
        db.session.commit()
        os.remove(image.filename)
        return image_data
    else:
        print("no image grabbed from file upload")
