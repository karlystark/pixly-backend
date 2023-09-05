"""Flask app for pixly app."""

import os

from flask import Flask, render_template, request, redirect
from flask_debugtoolbar import DebugToolbarExtension
from boto3 import boto3

app = Flask(__name__)
s3client = boto3.resource("s3")
BUCKET_NAME = "kk-pix.ly"

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

@app.get("/")
def get_images():

    return <h1>Hey!</h1>

@app.post("/")
def add_image():

    image = request.files["file"]
