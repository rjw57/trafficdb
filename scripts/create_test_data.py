# This script should be run via "webapp shell" and the "%run" magic
import os

from flask.ext.migrate import upgrade as upgrade_db

from trafficdb.models import *
from tests.fixtures import *
from tests.util import drop_all_data

# Rollback any incomplete session
db.session.rollback()

# Remember echo state
prev_echo = db.engine.echo
db.engine.echo = False

# Upgrade DB if necessary
upgrade_db()

# Drop any existing data
drop_all_data()
db.session.commit()

# Create test data
print('Creating test data...')
start_date = datetime.datetime(2012, 4, 23)
end_date = datetime.datetime(2012, 5, 10)
duration = int((end_date - start_date).total_seconds() // 60)
create_fake_observations(link_count=200, start=start_date, duration=duration)
db.session.commit()
print('Test data created')

db.engine.echo = prev_echo
