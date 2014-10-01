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

def prepare_resolve_link_aliases(session):
    """Must be called once before resolve_link_aliases in order to create a
    temporary table used by that query. Pass the return value from this
    function into resolve_link_aliases.

    """
    class ResolveNames(declarative_base(metadata=MetaData())):
        __tablename__ = 'tmp_link_alias_names'
        __table_args__ = {'prefixes': ['TEMPORARY']}
        name = db.Column(db.String, primary_key=True)

    # Create or temporary table to hold list of aliases
    try:
        ResolveNames.__table__.create(bind=session.bind)
    except exc.ProgrammingError:
        # HACK: This exception is raised if the table already exists, an
        # event which we silently swallow.
        pass

    return ResolveNames

def resolve_link_aliases(session, aliases, temp_table):
    """
    Given a sequence of link aliases, return a query.

    The query yields a corresponding table (name,
    link_id, link_uuid) of alias names and link ids with NULLs for invalid aliases.a

    NOTE: prepare_resolve_link_aliases() must have been called once in this
    session before resolve_link_aliases is called.

    """
    # Insert list of aliases into DB temporary table
    session.query(temp_table).delete()
    if len(aliases) > 0:
        session.execute(temp_table.__table__.insert(values=list({'name': a} for a in aliases)))

    # Form query
    sub_q = session.query(LinkAlias.name, Link.id, Link.uuid).join(Link).subquery()
    q = session.query(temp_table.name, sub_q.c.id, sub_q.c.uuid).\
            select_from(temp_table).\
            outerjoin(sub_q, temp_table.name == sub_q.c.name)

    return q
