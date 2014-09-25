import datetime

from mixer.backend.flask import Mixer

from trafficdb.models import *
from trafficdb.wsgi import db

def create_fake_observations():
    """Create a set of fake observations in the database."""

    # Disable auto-add to db for mixer
    mixer = Mixer(commit=False)

    # Create some random links
    links = mixer.cycle(3).blend(Link)
    db.session.add_all(links)

    # Extract ids
    link_ids = set(db.session.query(Link.id))

    # A set of observation times
    obs_times = []
    start = datetime.datetime(2013, 4, 29)
    for minutes in range(0, 60*3, 15):
        obs_times.append(start + datetime.timedelta(minutes=minutes))

    # For each link, create some random observations
    for link_id in link_ids:
        obs = mixer.cycle(len(obs_times)).blend(
            Observation, type=ObservationType.SPEED, link_id=link_id,
            observed_at=(t for t in obs_times))
        db.session.add_all(obs)

