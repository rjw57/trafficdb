#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'trafficdb',
    author = 'Rich Wareham',
    author_email = 'rich.trafficdb@richwareham.com',
    description = 'Web app to store historical traffic information',
    license = 'MIT',
    packages=find_packages(exclude=['tests']),

    install_require=[
        # Flask webapp platform
        'flask',
        'flask-migrate',
        'flask-script',
        'flask-sqlalchemy',

        # Database and database migration support
        'sqlalchemy',
        'alembic',
    ],

    # For testing
    setup_requires=[ 'nose>=1.0', ],
    tests_require=[ 'coverage', ],

    # For documentation
    extras_require={
        'docs': [ 'sphinx', 'docutils', ],
    },

    # Scripts and utilities
    entry_points = {
        'console_scripts': [
            'trafficdb_webapp = trafficdb.wsgi:main',
        ],
    },
)
