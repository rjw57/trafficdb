"""
Query helper functions
======================

These queries are optimised to use available indices.

"""
import uuid

from sqlalchemy import exc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData

from .models import *

def observations_for_link(session, link_id, type, min_datetime, max_datetime):
    return session.query(Observation).filter_by(link_id=link_id, type=type).\
            filter(Observation.observed_at >= min_datetime).\
            filter(Observation.observed_at <= max_datetime).\
            order_by(Observation.observed_at)

def observations_for_links(session, link_ids, type, min_datetime, max_datetime):
    return session.query(Observation).filter_by(type=type).\
            filter(Observation.link_id.in_(link_ids)).\
            filter(Observation.observed_at >= min_datetime).\
            filter(Observation.observed_at < max_datetime).\
            order_by(Observation.link_id, Observation.observed_at)

def observation_date_range(session):
    """A query which returns one row with the minimum (earliest) observation
    date and the maximum (latest) observation date.

    """
    return session.query(func.min(Observation.observed_at),
        func.max(Observation.observed_at))

def resolve_link_aliases(session, aliases):
    """
    Given a sequence of link aliases, return a query, session pair.

    The query yields a corresponding table (name,
    link_id) of alias names and link ids with NULLs for invalid aliases.a

    The session is one with a temporary table created within it. If you need to
    access this table, use the returned session.

    """

    session = session.session_factory()
    metadata = MetaData()

    class _LinkAliasNames(declarative_base(bind=session.bind, metadata=metadata)):
        __tablename__ = 'tmp_link_alias_names'
        __table_args__ = {'prefixes': ['TEMPORARY']}
        name = db.Column(db.String, primary_key=True)

    # Create or temporary table to hold list of aliases
    metadata.create_all(bind=session.bind, tables=[_LinkAliasNames.__table__])

    #session.execute(_LinkAliasNames.__table__.create())

    # Insert list of aliases
    session.execute(_LinkAliasNames.__table__.insert(values=list({'name': a} for a in aliases)))

    # Form query
    sub_q = session.query(LinkAlias.name, Link.id).join(Link).subquery()
    q = session.query(_LinkAliasNames.name, sub_q.c.id).\
            select_from(_LinkAliasNames).\
            outerjoin(sub_q, _LinkAliasNames.name == sub_q.c.name)

    return q, session
