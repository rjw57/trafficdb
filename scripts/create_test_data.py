# This script should be run via "webapp shell" and the "%run" magic
import os

from flask.ext.migrate import upgrade as upgrade_db

from trafficdb.models import *
from trafficdb.wsgi import app, db
from tests.fixtures import *
from tests.util import drop_all_data

try:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_TEST_DATABASE_URI']
except KeyError:
    print('SQLALCHEMY_TEST_DATABASE_URI environment variable must be defined')

# Upgrade DB if necessary
upgrade_db()

# Drop any existing data
drop_all_data()

# Rollback any incomplete session
db.session.rollback()

# Create test data
print('Creating test data...')
start_date = datetime.datetime(2012, 4, 23)
end_date = datetime.datetime(2012, 4, 30)
duration = int((end_date - start_date).total_seconds() // 60)
create_fake_observations(link_count=20, start=start_date, duration=duration)
db.session.commit()
print('Test data created')

