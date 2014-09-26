import datetime
import logging
import random

from mixer.backend.flask import Mixer
import pytz
from six.moves import range

from trafficdb.models import *

log = logging.getLogger(__name__)

DEFAULT_START = datetime.datetime(2013, 4, 29, tzinfo=pytz.utc)

def create_fake_observations(link_count=3, start=DEFAULT_START, duration=60*3, node_count=None):
    """Create a set of fake observations in the database."""
    # Default node count
    node_count = node_count or max(4, (link_count >> 1))

    # min lng, max lng, min lat, max lat
    bb = (-6.0, 1.5, 49.96, 60.8)

    # Generate random nodes
    nodes = []
    for _ in range(node_count):
        lng = bb[0] + random.random() * (bb[1] - bb[0])
        lat = bb[2] + random.random() * (bb[3] - bb[2])
        nodes.append((lng, lat))

    # Generate random link geometries
    def link_geoms():
        while True:
            a_idx, b_idx = None, None
            while a_idx == b_idx:
                a_idx, b_idx = random.sample(range(node_count), 2)
            a, b = tuple(nodes[i] for i in (a_idx, b_idx))
            yield 'SRID=4326;LINESTRING({0[0]} {0[1]}, {1[0]} {1[1]})'.format(a,b)

    # Disable auto-add to db for mixer
    mixer = Mixer(commit=False)

    # Create some random links
    links = mixer.cycle(link_count).blend(Link, geom=link_geoms)
    db.session.add_all(links)

    # Extract ids
    link_ids = set(db.session.query(Link.id))

    # A set of observation times
    obs_times = []
    for minutes in range(0, duration, 15):
        obs_times.append(start + datetime.timedelta(minutes=minutes))

    # For each link, create some random observations
    obs = []
    for link_id in link_ids:
        obs.extend(mixer.cycle(len(obs_times)).blend(
            Observation,
            type=ObservationType.SPEED, link_id=link_id,
            observed_at=(t for t in obs_times)))
    log.info('Adding {0} observation(s) to database'.format(len(obs)))
    db.session.add_all(obs)

