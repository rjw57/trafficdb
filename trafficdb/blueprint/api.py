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
    requested_count = min(PAGE_LIMIT, int(request.args.get('count', PAGE_LIMIT)))

    # Query link objects
    links_q = db.session.query(Link.id, func.ST_AsGeoJSON(Link.geom)).order_by(Link.id).\
            filter(Link.id >= request.args.get('from', 0)).\
            limit(requested_count+1)

    def row_to_dict(row):
        feature = dict(
            type='Feature',
            id=row[0],
            geometry=json.loads(row[1])
        )
        return feature

    links = list(row_to_dict(l) for l in links_q)

    # How many links to return and do we still have more?
    count = min(requested_count, len(links))
    more = (len(links) == requested_count+1)

    # Limit size of output
    links = links[:requested_count]

    # Form response
    feature_collection = dict(type='FeatureCollection', features=links)
    page = dict(
        first = links[0]['id'] if len(links) > 0 else None,
        last = links[-1]['id'] if len(links) > 0 else None,
        count = count, more=more
    )
    response = dict(data=feature_collection, page=page)
    return jsonify(response)
