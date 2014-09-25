"""
Database models
===============
"""

__all__ = ['Link', 'Observation', 'ObservationType']

from enum import Enum

from sqlalchemy import types

from .wsgi import db

class PythonEnum(types.TypeDecorator):
    """A SQLAlchemy type decorator for Python 3.4-style enums. Taken from
    https://groups.google.com/forum/#!msg/sqlalchemy/5yvdhl9ErMo/ArJJad8byZkJ.

    """

    impl = types.Enum

    def __init__(self, enum_class, **kw):
        super(PythonEnum, self).__init__(*(m.name for m in enum_class), **kw)
        self._enum_class = enum_class

    def process_bind_param(self, value, dialect):
        return value.name

    def process_result_value(self, value, dialect):
        return self._enum_class[value]

    @property
    def python_type(self):
        return self._enum_class

class ObservationType(Enum):
    SPEED       = 0
    FLOW        = 1
    OCCUPANCY   = 2

class Link(db.Model):
    __tablename__ = 'links'

    id          = db.Column(db.Integer, primary_key=True)

class Observation(db.Model):
    __tablename__ = 'observations'

    id          = db.Column(db.Integer, primary_key=True)
    value       = db.Column(db.Float, nullable=False)
    type        = db.Column(PythonEnum(ObservationType, name='observation_types'), nullable=False)
    observed_at = db.Column(db.DateTime, nullable=False)
    link_id     = db.Column(db.Integer, db.ForeignKey('links.id'), nullable=False)

# An index to enable efficient retrieval of observations in a range.
db.Index('ix_observation_observed_at', Observation.observed_at)

# An index to enable efficient retrieval of observations in a range and link.
db.Index('ix_observation_observed_at_link_id', Observation.observed_at, Observation.link_id)
