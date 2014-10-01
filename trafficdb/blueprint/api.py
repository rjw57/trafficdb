"""API to access and modify traffic data records.

"""
import base64
import datetime
try:
    from urllib.parse import urljoin, urlencode, parse_qs
except ImportError:
    from urlparse import urljoin, parse_qs
    from urllib import urlencode
import uuid

from flask import *
import six
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
import pytz

from trafficdb.models import *
from trafficdb.queries import (
        observation_date_range,
        observations_for_link,
        prepare_resolve_link_aliases,
        resolve_link_aliases,
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

JAVASCRIPT_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)

def javascript_timestamp_to_datetime(ts):
    return JAVASCRIPT_EPOCH + datetime.timedelta(milliseconds=ts)

def datetime_to_javascript_timestamp(dt):
    return int((dt - JAVASCRIPT_EPOCH).total_seconds() * 1000)

def uuid_to_urlsafe_id(uuid_text):
    id_bytes = base64.urlsafe_b64encode(uuid.UUID(uuid_text).bytes).rstrip(b'=')
    try:
        return str(id_bytes, 'utf8')
    except TypeError:
        # On python 2, str doesn't take 2 arguments so use .decode()
        return id_bytes.decode('utf8')

def urlsafe_id_to_uuid(urlsafe_id):
    if not isinstance(urlsafe_id, bytes):
        urlsafe_id = urlsafe_id.encode('utf8')
    padding = 4 - (len(urlsafe_id) % 4)
    return uuid.UUID(bytes=base64.urlsafe_b64decode(urlsafe_id + b'='*padding)).hex

@app.route('/')
def index():
    return jsonify(dict(
        version=1,
        resources=dict(
            links=url_for('.links', _external=True),
            linkAliases=url_for('.link_aliases', _external=True),
        ),
    ))

def extend_request_query(base_url, query):
    qs = parse_qs(request.query_string)
    for k, v in query.items():
        if not isinstance(k, bytes):
            k = k.encode('utf8')
        qs[k] = [v,]
    return urljoin(base_url, '?' + urlencode(qs, doseq=True))

@app.route('/links/')
def links():
    try:
        requested_count = int(request.args.get('count', PAGE_LIMIT))
    except ValueError:
        # requested count was not an integer
        return abort(400)

    # Limit count to the maximum we're prepared to give
    requested_count = min(PAGE_LIMIT, requested_count)

    # Count must be +ve
    if requested_count < 0:
        return abort(400)

    # Query link objects
    links_q = db.session.query(Link.uuid, func.ST_AsGeoJSON(Link.geom)).order_by(Link.uuid)

    unverified_from_id = request.args.get('from')
    if unverified_from_id is not None:
        try:
            from_uuid = urlsafe_id_to_uuid(unverified_from_id)
        except:
            # If from id is invalid, this is a bad request
            return abort(400)
        links_q = links_q.filter(Link.uuid >= from_uuid)

    links_q = links_q.limit(requested_count+1)

    def row_to_dict(row):
        id_string = uuid_to_urlsafe_id(row[0])
        properties=dict(
            observationsUrl=url_for(
                '.observations', unverified_link_id=id_string, _external=True),
            url=url_for(
                '.link', unverified_link_id=id_string, _external=True),
        )
        feature = dict(
            type='Feature',
            id=id_string,
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
    page = dict(count = count)
    feature_collection = dict(
        type='FeatureCollection',
        features=links,
        properties=dict(page=page),
    )

    # Form next url if necessary
    if next_link_id is not None:
        next_args = parse_qs(request.query_string)
        next_args['from'.encode('utf8')] = [next_link_id,]
        page['next'] = extend_request_query(
            url_for('.links', _external=True),
            {'from': next_link_id}
        )

    return jsonify(feature_collection)

def verify_link_id(unverified_link_id):
    """Return a primary-key, uuid pair for a link given the unverified link id
    from a URL. Aborts with 404 if the link id is invalid or not found.

    """
    # Verify link id
    try:
        link_uuid = urlsafe_id_to_uuid(unverified_link_id)
    except:
        # If the uuid is invalid, just return 404
        return abort(404)

    link_q = db.session.query(Link.id, Link.uuid).filter(Link.uuid == link_uuid).limit(1)
    try:
        return link_q.one()
    except NoResultFound:
        # 404 on non-existent link
        return abort(404)

    # Should be unreachable
    assert False

@app.route('/links/<unverified_link_id>/observations')
def observations(unverified_link_id):
    # Verify link id
    link_id, link_uuid = verify_link_id(unverified_link_id)
    link_urlsafe_id=uuid_to_urlsafe_id(link_uuid)
    link_data = dict(id=link_urlsafe_id)

    # Work out if a time range has been specified
    try:
        duration = int(request.args.get('duration', MAX_DURATION))
    except ValueError:
        # If duration can't be parsed as an integer, that's a bad request
        return abort(400)

    # Restrict duration to the maximum we're comfortable with
    duration = min(MAX_DURATION, duration)
    if duration < 0:
        return abort(400)

    start_ts = request.args.get('start')
    if start_ts is None:
        # Get minimum and maximum times
        min_d, max_d = observation_date_range(db.session).one()
        start_ts = datetime_to_javascript_timestamp(
                max_d - datetime.timedelta(milliseconds=duration))
    else:
        # Verify start ts is indeed an integer
        try:
            start_ts = int(start_ts)
        except ValueError:
            return abort(400)

    # Record parameters of sanitised query
    query_params = dict(start=start_ts, duration=duration)
    query_params['earlier'] = extend_request_query(
        url_for('.observations', unverified_link_id=link_urlsafe_id, _external=True),
        dict(start=start_ts-duration),
    )
    query_params['later'] = extend_request_query(
        url_for('.observations', unverified_link_id=link_urlsafe_id, _external=True),
        dict(start=start_ts+duration),
    )

    start_date = javascript_timestamp_to_datetime(start_ts)
    end_date = javascript_timestamp_to_datetime(start_ts + duration)

    data = {}
    for type in ObservationType:
        values = []
        q = observations_for_link(db.session, link_id, type, start_date, end_date)
        for obs in q:
            values.append((datetime_to_javascript_timestamp(obs.observed_at), obs.value))
        data[type.value] = dict(values=values)

    response = dict(link=link_data, data=data, query=query_params)
    return jsonify(response)

@app.route('/links/<unverified_link_id>/')
def link(unverified_link_id):
    link_id, link_uuid = verify_link_id(unverified_link_id)
    link_url_id = uuid_to_urlsafe_id(link_uuid)

    # Query aliases
    aliases = list(r[0] for r in
            db.session.query(LinkAlias.name).filter(LinkAlias.link_id==link_id))

    response = dict(
        id=link_url_id,
        observationsUrl=url_for('.observations', unverified_link_id=link_url_id, _external=True),
        aliases=aliases,
    )
    return jsonify(response)

@app.route('/linkaliases/')
def link_aliases():
    try:
        requested_count = int(request.args.get('count', PAGE_LIMIT))
    except ValueError:
        # requested count was not an integer
        return abort(400)

    # Limit count to the maximum we're prepared to give
    requested_count = min(PAGE_LIMIT, requested_count)

    # Count must be +ve
    if requested_count < 0:
        return abort(400)

    # Query link objects
    aliases_q = db.session.query(LinkAlias.name, Link.uuid).join(Link).\
        order_by(LinkAlias.name)

    from_id = request.args.get('from', None)
    if from_id is not None:
        aliases_q = aliases_q.filter(LinkAlias.name >= str(from_id))

    aliases_q = aliases_q.limit(requested_count+1)

    def row_to_item(row):
        link_id = uuid_to_urlsafe_id(row[1])
        link_url = url_for('.link', unverified_link_id=link_id, _external=True)
        return dict(id=row[0], linkId=link_id, linkUrl=link_url)

    aliases = list(row_to_item(l) for l in aliases_q)

    # How many aliases to return and do we still have more?
    count = min(requested_count, len(aliases))

    # Limit size of output
    next_link_id = aliases[requested_count]['id'] if len(aliases) > requested_count else None
    aliases = aliases[:requested_count]

    # Form response
    page = dict(count = count)

    # Form next url if necessary
    if next_link_id is not None:
        next_args = parse_qs(request.query_string)
        next_args['from'.encode('utf8')] = [next_link_id,]
        page['next'] = extend_request_query(
            url_for('.link_aliases', _external=True),
            {'from': next_link_id}
        )

    return jsonify(dict(aliases=aliases, page=page))

@app.route('/linkaliases/resolve', methods=['POST'])
def link_aliases_resolve():
    # Request body should be JSON
    req_body = request.get_json()
    if req_body is None:
        return abort(400)

    # Retrieve and sanitise alias list
    try:
        aliases = req_body['aliases']
    except KeyError:
        return abort(400)
    if not isinstance(aliases, list):
        return abort(400)
    if len(aliases) > PAGE_LIMIT:
        return abort(400)
    if any(not isinstance(a, six.string_types) for a in aliases):
        return abort(400)

    def link_from_uuid(link_uuid):
        if link_uuid is None:
            return None
        link_id = uuid_to_urlsafe_id(link_uuid)
        return dict(id=link_id, url=url_for('.link', unverified_link_id=link_id, _external=True))

    tmp_table = prepare_resolve_link_aliases(db.session)
    q = resolve_link_aliases(db.session, aliases, tmp_table)
    resolutions = list((r[0], link_from_uuid(r[2])) for r in q)
    response = dict(resolutions=resolutions)
    return jsonify(response)
