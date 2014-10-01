# This script should be run via "webapp shell" and the "%run" magic
#
# create_test_data may be used to populate the test db with information
import datetime

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement, _literal_as_text
from sqlalchemy import func

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

def explain_analyze(q, session=db.session):
    print('Query explanation:')
    for l in session.execute(explain(q, analyze=True)):
        print(l[0])

# Get some names
alias_names = list(r[0] for r in \
        db.session.query(LinkAlias.name).order_by(func.random()).limit(5).all())
alias_names.extend(['invalid2', 'invalid1'])
print(alias_names)

q, session = resolve_link_aliases(db.session, alias_names)
explain_analyze(q, session=session)

for r in q.all():
    print(r)

