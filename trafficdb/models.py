"""
Database models
===============
"""

__all__ = ['db', 'Link', 'Observation', 'ObservationType']

from enum import Enum
import uuid

from flask import current_app as app
from flask.ext.sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from sqlalchemy import func, types
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import expression

# Create app database
db = SQLAlchemy()

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

class uuid_generate_v4(expression.FunctionElement):
    type = pg.UUID()

@compiles(uuid_generate_v4, 'postgresql')
def pg_uuid_generate_v4(element, compiler, **kw):
    return 'uuid_generate_v4()'

class ObservationType(Enum):
    """Names in this enum map to names used in the database and values map to
    those exposed in API."""
    SPEED       = 'speed'
    FLOW        = 'flow'
    OCCUPANCY   = 'occupancy'

class Link(db.Model):
    __tablename__ = 'links'

    id          = db.Column(db.Integer, primary_key=True)
    # An opaque UUID to avoid exposing primary keys to API.
    uuid        = db.Column(pg.UUID, server_default=uuid_generate_v4(),
                    default=lambda: uuid.uuid4().hex, nullable=False)
    geom        = db.Column(Geometry('LINESTRING', srid=4326), nullable=False)

# An index to enable efficient retrieval and ordering of links by uuid.
db.Index('ix_link_uuid', Link.uuid, unique=True)

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
