from flask import Blueprint

bp = Blueprint('videoapp', __name__)

from app.videoapp import routes
