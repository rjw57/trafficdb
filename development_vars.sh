# Source this file to det up development datavase
export SQLALCHEMY_DATABASE_URI=`curl -s http://api.postgression.com`
export SQLALCHEMY_TEST_DATABASE_URI="${SQLALCHEMY_DATABASE_URI}"
