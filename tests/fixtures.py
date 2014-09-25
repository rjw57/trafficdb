import datetime
import logging

from mixer.backend.flask import Mixer

from trafficdb.models import *
from trafficdb.wsgi import db

log = logging.getLogger(__name__)

def create_fake_observations(link_count=3, start=datetime.datetime(2013, 4, 29), duration=60*3):
    """Create a set of fake observations in the database."""

    # Disable auto-add to db for mixer
    mixer = Mixer(commit=False)

    # Create some random links
    links = mixer.cycle(link_count).blend(Link, geom='SRID=4326;LINESTRING EMPTY')
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
            Observation, type=ObservationType.SPEED, link_id=link_id,
            observed_at=(t for t in obs_times)))
    log.info('Adding {0} observation(s) to database'.format(len(obs)))
    db.session.add_all(obs)

