"""Flask app for pixly app."""
import os
from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
from model import connect_db, db, Photo

load_dotenv()

from utilities import make_unique_filename, get_image_metadata, send_file_to_s3


app = Flask(__name__)

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
def get_images():
    return render_template("form.html")

#TODO: ADD TO MODELS
def add_to_db(data):
    """Add an image data object to the database"""

    image = Photo(
        filename=data["filename"],
        camera=data["camera"],
        width=data["width"],
        height=data["height"],
        location=data["location"]
    )

    db.session.add(image)
    db.session.commit()

#POST request sent to root route: pulls file object from request,
#changes filename to universally unique name, sends file to S3,
#grabs image metadata and uploads image data to database,
#Returns success message or error message
@app.post("/")
def add_image():
    image = request.files["file"]
    print("image=", image)

    if image.filename != "":
        image.filename = make_unique_filename()
        image.save(image.filename)
        send_file_to_s3(image, app.config['S3_BUCKET'])

        image_data = get_image_metadata(image.filename)
        add_to_db(image_data)
        os.remove(image.filename)
        return image_data
    else:
        print("no image grabbed from file upload")
