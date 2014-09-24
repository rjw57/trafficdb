#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'trafficdb',
    author = 'Rich Wareham',
    author_email = 'rich.trafficdb@richwareham.com',
    description = 'Web app to store historical traffic information',
    license = 'MIT',
    packages=find_packages(exclude=['tests']),

    install_requires=[
        # General language support
        'enum34',

        # Flask webapp platform
        'flask',
        'flask-migrate',
        'flask-script',
        'flask-sqlalchemy',

        # Database and database migration support
        'alembic',
        'psycopg2',
        'sqlalchemy',
    ],

    # For testing
    setup_requires=[ 'nose>=1.0', ],
    tests_require=[ 'coverage', 'requests', 'flask-testing', ],

    # For documentation
    extras_require={
        'docs': [ 'sphinx', 'docutils', ],
    },

    # Scripts and utilities
    entry_points = {
        'console_scripts': [
            'trafficdb_webapp = trafficdb.manager:main',
        ],
    },
)
