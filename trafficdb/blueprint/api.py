"""API to access and modify traffic data records."""

from flask import *

__all__ = ['api']

# Create a Blueprint for the web api
api = Blueprint('api', __name__)

# alias api as "app" for use below
app = api

@app.route('/')
def index():
    return jsonify(dict(version=1))
