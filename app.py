"""Flask app for pixly app."""

import os
from flask import Flask, render_template, request, redirect
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
import boto3
import uuid
from exif import Image as Exif
from PIL import Image, ExifTags
from geopy.geocoders import Nominatim
from model import connect_db, db, Photo

load_dotenv()

app = Flask(__name__)

app.config['S3_BUCKET'] = os.environ["S3_BUCKET_NAME"]
app.config['S3_KEY'] = os.environ["AWS_ACCESS_KEY"]
app.config['S3_SECRET'] = os.environ["AWS_ACCESS_SECRET"]
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "postgresql:///photos")

geolocator = Nominatim(user_agent="geoapiExercises")

s3 = boto3.client(
    "s3",
    "us-west-1",
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET']
)

connect_db(app)

toolbar = DebugToolbarExtension(app)



@app.get("/")
def get_images():
    return render_template("form.html")

# Make a universally unique jpg filename
def make_unique_filename():
    new_filename = uuid.uuid4().hex + ".jpg"
    return new_filename

def location_tuple_to_decimal(tuple):
    return tuple[0] + tuple[1]/60 + tuple[2]/3600

#Given latitude and longitude values, return a string that contains the location's city and country
def get_location(image_filename):
    with open(image_filename, "rb") as image_file:
        image_data = Exif(image_file)

    if image_data.get("gps_latitude") and image_data.get("gps_longitude"):

        #TODO: calculate latitude and longitude values from tuples
        print("LATITUDE VALUE=", image_data.gps_latitude, type(image_data.gps_latitude))
        print("LONGITUDE VALUE=", image_data.gps_longitude, type(image_data.gps_longitude))
        print("type of tuples", type(image_data.gps_latitude[0]))
        print("LONGITUDE REF=", image_data.gps_longitude_ref)
        print("LATITUDE REF=", image_data.gps_latitude_ref)

        latitude_decimal_form = location_tuple_to_decimal(image_data.gps_latitude)
        longitude_decimal_form = location_tuple_to_decimal(image_data.gps_longitude)

        latitude = latitude_decimal_form if image_data.gps_latitude_ref == "N" else -abs(latitude_decimal_form)
        longitude = longitude_decimal_form if image_data.gps_longitude_ref == "E" else -abs(longitude_decimal_form)

        location = geolocator.reverse(latitude+","+longitude)
        location_data = location.raw['address']

        city = location_data.get('city', '')
        country = location_data.get('country', '')

        return f"{city}, {country}"
    else:
        return None

#Given an image filename, extract EXIF image data and create an object that holds desired values
def get_image_metadata(image_filename):
    image_file = Image.open(image_filename)
    image_data = image_file.getexif()

    if image_data:
        for key, val in image_data.items():
            if key in ExifTags.TAGS:
                print(f'{ExifTags.TAGS[key]}: {val}')

        width = image_file.width
        height = image_file.height
        make = ExifTags.Base.Make.value
        model = ExifTags.Base.Model.value
        location = get_location(image_filename)

#271 => Make
#272 => Model
#34853 => lat & long => gpsinfo = info.get_ifd(34853)
#Image.width ==> image width, in pixels
#Image.height ==> image height, in pixels



        print("before creating select_data get make", image_data.get("make"))
        select_data = {
            "filename": image_filename,
            "camera": f"{make} {model}" if (make and model) else None,
            "width": width if width else None,
            "height": height if height else None,
            "location": location if location else None
        }
    else:
        select_data = {"filename": image_filename,
                       "camera": None,
                       "width": None,
                       "height": None,
                       "location": None
                       }

    print("select_data=", select_data)
    print("type of select data", type(select_data))

    return select_data



#Add an image data object the the database
def add_to_db(data):
    print ("what's our filename?", data["filename"])
    image = Photo(
        filename=data["filename"],
        camera=data["camera"],
        width=data["width"],
        height=data["height"],
        location=data["location"]
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
