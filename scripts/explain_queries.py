# This script should be run via "webapp shell" and the "%run" magic
#
# create_test_data may be used to populate the test db with information
import datetime

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text

from trafficdb.models import *
from trafficdb.queries import *

# From https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Explain
class explain(Executable, ClauseElement):
    def __init__(self, stmt, analyze=False):
        self.statement = _literal_as_text(stmt)
        self.analyze = analyze

@compiles(explain, 'postgresql')
def pg_explain(element, compiler, **kw):
    text = "EXPLAIN "
    if element.analyze:
        text += "ANALYZE "
    text += compiler.process(element.statement)
    return text

def explain_analyze(q):
    print('Query explanation:')
    for l in db.session.execute(explain(q, analyze=True)):
        print(l[0])

# Fetch date range
q = observation_date_range(db.session)
print('Querying date range')
explain_analyze(q)
start_date, end_date = q.first()
print('Start/end: {0}/{1}'.format(start_date, end_date))

# Fetch observations for random link
link_id = db.session.query(Link.id).limit(1).first().id
print('Fetching observations for link id {0}'.format(link_id))
q = observations_for_link(db.session, link_id, ObservationType.SPEED,
    start_date + datetime.timedelta(days=1),
    start_date + datetime.timedelta(days=2))
explain_analyze(q)
print('Matching rows: {0}'.format(q.count()))

# Fetch observations for 10 random link
link_ids = db.session.query(Link.id).limit(10).all()
print('Fetching observations for link ids {0}'.format(link_ids))
q = observations_for_links(db.session, link_ids, ObservationType.SPEED,
    start_date + datetime.timedelta(days=1),
    start_date + datetime.timedelta(days=2))
explain_analyze(q)
print('Matching rows: {0}'.format(q.count()))
