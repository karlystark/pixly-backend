from dotenv import load_dotenv
import os
import uuid
import boto3
from exif import Image as Exif
from PIL import Image
from geopy.geocoders import Nominatim


load_dotenv()

geolocator = Nominatim(user_agent="pixlyTest")


s3 = boto3.client(
    "s3",
    "us-west-1",
    aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
    aws_secret_access_key=os.environ['AWS_ACCESS_SECRET']
)


def make_unique_filename():
    """Make a universally unique jpg filename"""
    new_filename = uuid.uuid4().hex + ".jpg"
    return new_filename

def location_tuple_to_decimal(tuple):
    """Given a tuple containing GPS location data in degrees, minutes, and
    seconds, returns the compressed value. Ex. 24.9848."""
    return tuple[0] + tuple[1]/60 + tuple[2]/3600


def get_location(image_filename):
    """Given an image filename, grabs EXIF latitude and longitude values and
    processes them, returning a string that contains the location's city and
    country"""
    with open(image_filename, "rb") as image_file:
        image_data = Exif(image_file)

    if image_data.get("gps_latitude") and image_data.get("gps_longitude"):

        latitude_decimal_form = (
            location_tuple_to_decimal(image_data.gps_latitude))
        longitude_decimal_form = (
            location_tuple_to_decimal(image_data.gps_longitude))

        latitude = (
            latitude_decimal_form
            if image_data.gps_latitude_ref == "N"
            else -abs(latitude_decimal_form))
        longitude = (
            longitude_decimal_form
            if image_data.gps_longitude_ref == "E"
            else -abs(longitude_decimal_form))

        latitude_string = str(latitude)
        longitude_string = str(longitude)

        location = geolocator.reverse(latitude_string+","+longitude_string)
        location_data = location.raw['address']

        city = location_data.get('city', '')
        country = location_data.get('country', '')

        return f"{city}, {country}"
    else:
        return None


def get_image_metadata(image_filename):
    """Take an image filename. Extract EXIF image data.  Create and return
     an object that holds desired values"""

    image_file = Image.open(image_filename)
    image_data = image_file.getexif()

    if image_data:
        width = image_file.width
        height = image_file.height
        make = image_data.get(271)
        model = image_data.get(272)
        location = get_location(image_filename)
        #TODO: comments to understand.  Global constants.


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


def send_file_to_s3(file, bucket):
    """Upload an image file to AWS S3 bucket"""
    try:
        print("filename=", file.filename)

        s3.upload_file(file.filename, bucket, file.filename)
    except Exception as e:
        return f"Error occurred: {e}"

    return "file successfully uploaded"


#TODO: Move select_data = {} section into Models static method.