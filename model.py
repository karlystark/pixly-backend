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
    )

    width = db.Column(
        db.Integer,
    )

    height = db.Column(
        db.Integer,
    )

    location = db.Column(
        db.String,
    )


