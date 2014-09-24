from enum import Enum

from .wsgi import db

class ObservationType(Enum):
    SPEED       = 0
    FLOW        = 1
    OCCUPANCY   = 2

_OBSERVATION_TYPES = list(ObservationType.__members__.keys())

class Link(db.Model):
    __tablename__ = 'links'

    id          = db.Column(db.Integer, primary_key=True)

class Observation(db.Model):
    __tablename__ = 'observations'

    id          = db.Column(db.Integer, primary_key=True)
    value       = db.Column(db.Float)
    type        = db.Column(db.Enum(*_OBSERVATION_TYPES, name='observation_types'))
    observed_at = db.Column(db.DateTime)
    link_id     = db.Column(db.Integer, db.ForeignKey('links.id'))
