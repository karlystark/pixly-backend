"""Flask app for pixly app."""

import os
from flask import Flask, render_template, request, redirect
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
import boto3
import uuid
from exif import Image
from geopy.geocoders import Nominatim
from model import connect_db, db, Photo

load_dotenv()

app = Flask(__name__)

app.config['S3_BUCKET'] = os.environ["S3_BUCKET_NAME"]
app.config['S3_KEY'] = os.environ["AWS_ACCESS_KEY"]
app.config['S3_SECRET'] = os.environ["AWS_ACCESS_SECRET"]
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

geolocator = Nominatim(user_agent="geoapiExercises")

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

# Make a universally unique jpg filename
def make_unique_filename():
    new_filename = uuid.uuid4().hex + ".jpg"
    return new_filename

#Given latitude and longitude values, return a string that contains the location's city and country
def get_location(latitude, longitude):
    location = geolocator.reverse(latitude+","+longitude)
    location_data = location.raw['address']

    city = location_data.get('city', '')
    country = location_data.get('country', '')

    return f"{city}, {country}"

#Given an image filename, extract EXIF image data and create an object that holds desired values
def get_image_metadata(image_filename):
    with open(image_filename, "rb") as image_file:
        image_data = Image(image_file)

    location = None

    if image_data.gps_latitude and image_data.gps_longitude:
        latitude = image_data.gps_latitude if image_data.gps_latitude_ref == "N" else -abs(image_data.gps_latitude)
        longitude = image_data.gps_longitude if image_data.gps_longitude_ref == "E" else -abs(image_data.gps_longitude)
        location = get_location(latitude, longitude)

    select_data = {
        "filename": image_filename,
        "camera": ((f"{image_data.make} {image_data.model}") if (image_data.make and image_data.model) else None),
        "width": (image_data.pixel_x_dimension if (image_data.pixel_x_dimension) else None),
        "height": (image_data.pixel_y_dimension if image_data.pixel_y_dimension else None),
        "location": location if location else None,
        "aperture": image_data.aperture_value if image_data.aperture_value else None,
        "shutter_speed": image_data.shutter_speed_value if image_data.shutter_speed_value else None,
        "focal_length": image_data.focal_length if image_data.focal_length else None
    }

    return select_data

    print("select_data=", select_data)

#Add an image data object the the database
def add_to_db(data):
    image = Photo(
        filename=data.filename,
        camera=data.camera,
        width=data.width,
        height=data.height,
        latitude=data.latitude,
        longitude=data.longitude,
        shutter_speed=data.shutter_speed,
        focal_length=data.focal_length
    )

    db.session.add(image)
    db.session.commit()

#Upload an image file to AWS S3 bucket
def send_file_to_s3(file, bucket):
    try:
        print("filename=", file.filename)

        s3.upload_file(file.filename, bucket, file.filename)
    except Exception as e:
        return f"Error occurred: {e}"

    return "file successfully uploaded"


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
