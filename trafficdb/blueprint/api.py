"""API to access and modify traffic data records."""

from flask import *
from sqlalchemy import func

from trafficdb.models import *

__all__ = ['api']

# Create a Blueprint for the web api
api = Blueprint('api', __name__)

# alias api as "app" for use below
app = api

# Maximum number of results to return
PAGE_LIMIT = 20

@app.route('/')
def index():
    return jsonify(dict(version=1))

@app.route('/links')
def links():
    # Query link objects
    links_q = db.session.query(Link.id, func.ST_AsText(Link.geom)).order_by(Link.id).\
            filter(Link.id >= request.args.get('from', 0)).\
            limit(PAGE_LIMIT+1)

    def row_to_dict(row):
        return dict(id=row[0], geom=row[1])

    links = list(row_to_dict(l) for l in links_q)

    # How many links to return and do we still have more?
    count = min(PAGE_LIMIT, len(links))
    more = (len(links) == PAGE_LIMIT+1)

    # Limit size of output
    links = links[:PAGE_LIMIT]

    # Form response
    page = dict(
        first = links[0]['id'],
        last = links[-1]['id'],
        count = count, more=more
    )
    response = dict(data=links, page=page)
    return jsonify(response)
