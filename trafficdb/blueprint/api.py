"""API to access and modify traffic data records.

"""
import datetime
try:
    from urllib.parse import urljoin, urlencode, parse_qs
except ImportError:
    from urlparse import urljoin, parse_qs
    from urllib import urlencode

from flask import *
from sqlalchemy import func

from trafficdb.models import *
from trafficdb.queries import (
        observation_date_range,
        observations_for_link
)

__all__ = ['api']

# Create a Blueprint for the web api
api = Blueprint('api', __name__)

# alias api as "app" for use below
app = api

# Maximum number of results to return
PAGE_LIMIT = 20

# Maximum duration to query over in *milliseconds*
MAX_DURATION = 3*24*60*60*1000

def javascript_timestamp_to_datetime(ts):
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=ts)

def datetime_to_javascript_timestamp(dt):
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

@app.route('/')
def index():
    return jsonify(dict(
        version=1,
        resources=dict(
            links=url_for('.links', _external=True),
        ),
    ))

@app.route('/links')
def links():
    requested_count = min(PAGE_LIMIT, int(request.args.get('count', PAGE_LIMIT)))
    import logging
    log = logging.getLogger(__name__)
    log.info('ARGS: {0}'.format(request.args))

    # Query link objects
    links_q = db.session.query(Link.id, func.ST_AsGeoJSON(Link.geom)).order_by(Link.id).\
            filter(Link.id >= request.args.get('from', 0)).\
            limit(requested_count+1)

    def row_to_dict(row):
        properties=dict(observationsUrl=url_for(
            '.observations', unverified_link_id=row[0], _external=True))
        feature = dict(
            type='Feature',
            id=row[0],
            geometry=json.loads(row[1]),
            properties=properties,
        )
        return feature

    links = list(row_to_dict(l) for l in links_q)

    # How many links to return and do we still have more?
    count = min(requested_count, len(links))

    # Limit size of output
    next_link_id = links[requested_count]['id'] if len(links) > requested_count else None
    links = links[:requested_count]

    # Form response
    feature_collection = dict(type='FeatureCollection', features=links)
    page = dict(
        first = links[0]['id'] if len(links) > 0 else None,
        last = links[-1]['id'] if len(links) > 0 else None,
        count = count,
    )

    # Form next and url
    if next_link_id is not None:
        next_args = parse_qs(request.query_string)
        next_args['from'.encode('utf8')] = [next_link_id,]
        page['next'] = urljoin(
            url_for('.links', _external=True),
            '?' + urlencode(next_args, doseq=True)
        )

    response = dict(data=feature_collection, page=page)
    return jsonify(response)

@app.route('/observations/<int:unverified_link_id>')
def observations(unverified_link_id):
    # Verify link id
    link_id = db.session.query(Link.id).\
        filter(Link.id == unverified_link_id).scalar()

    # 404 on non-existent link
    if link_id is None:
        return abort(404)
    link_data = dict(id=link_id)

    # Work out if a time range has been specified
    duration = min(MAX_DURATION, request.args.get('duration', MAX_DURATION))
    if duration < 0:
        return abort(400)

    start_ts = request.args.get('start')
    if start_ts is None:
        # Get minimum and maximum times
        min_d, max_d = observation_date_range(db.session).one()
        start_ts = datetime_to_javascript_timestamp(
                max_d - datetime.timedelta(milliseconds=duration))

    start_date = javascript_timestamp_to_datetime(start_ts)
    end_date = javascript_timestamp_to_datetime(start_ts + duration)

    data = {}
    for type in ObservationType:
        values = []
        q = observations_for_link(db.session, link_id, type, start_date, end_date)
        for obs in q:
            values.append((datetime_to_javascript_timestamp(obs.observed_at), obs.value))
        data[type.value] = dict(values=values)

    response = dict(link=link_data, data=data)
    return jsonify(response)
