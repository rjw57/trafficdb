Developer instructions
======================

Testing
~~~~~~~

The web app should be fully tested. This includes the database layer.  One can
test using a temporary PostgreSQL database in the cloud using `postgression
<http://www.postgression.com>`_.

After creating the database, you can upgrade it to the correct schema and run
the unit tests as follows:

.. code:: console

    $ export SQLALCHEMY_TEST_DATABASE_URI=`curl -s http://api.postgression.com`
    $ webapp db upgrade
    INFO  [alembic.migration] Context impl PostgresqlImpl.
    INFO  [alembic.migration] Will assume transactional DDL.
    INFO  [alembic.migration] Running upgrade None -> 7dc1a66bb8, Initial database migration
    $ python setup.py nosetests

This is done automatically in the :download:`Travis-CI configuration
<../.travis.yml>`.
