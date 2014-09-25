"""
Query helper functions
======================

These queries are optimised to use available indices.

"""

from .models import *

def observations_for_link(session, link_id, type, min_datetime, max_datetime):
    return session.query(Observation).filter_by(link_id=link_id, type=type).\
            filter(Observation.observed_at >= min_datetime).\
            filter(Observation.observed_at <= max_datetime).\
            order_by(Observation.observed_at)

