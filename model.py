"""Model for Pix.ly"""
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""

    app.app_context().push()
    db.app = app
    db.init_app(app)


class Photo(db.Model):
    __tablename__= "photos"

    filename = db.Column(
        db.String(50),
        primary_key=True
    )

    camera = db.Column(
        db.String(50),
        nullable=False
    )

    width = db.Column(
        db.Integer,
        nullable=False
    )

    height = db.Column(
        db.Integer,
        nullable=False
    )

    latitude = db.Column(
        db.String(20),
        nullable=False
    )

    longitude = db.Column(
        db.String(20),
        nullable=False
    )

    aperture = db.Column(
        db.Float,
        nullable=False
    )

    shutter_speed = db.Column(
        db.Float,
        nullable=False
    )

    focal_length = db.Column(
        db.Float,
        nullable=False
    )


