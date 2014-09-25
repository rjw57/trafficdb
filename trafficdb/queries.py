"""
Query helper functions
======================

These queries are optimised to use available indices.

"""
from sqlalchemy import func
from .models import *

def observations_for_link(session, link_id, type, min_datetime, max_datetime):
    return session.query(Observation).filter_by(link_id=link_id, type=type).\
            filter(Observation.observed_at >= min_datetime).\
            filter(Observation.observed_at <= max_datetime).\
            order_by(Observation.observed_at)

def observation_date_range(session):
    """A query which returns one row with the minimum (earliest) observation
    date and the maximum (latest) observation date.

    """
    return session.query(func.min(Observation.observed_at),
        func.max(Observation.observed_at))
