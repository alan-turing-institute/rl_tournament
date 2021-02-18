"""
Create a test database (sqlite) for pytest
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from battleground.schema import Base

if os.name == "posix":
    TMPDIR = "/tmp"
else:
    TMPDIR = "%TMP%"

TMPDB = os.path.join(TMPDIR, "plarktest.db")

testengine = create_engine("sqlite:///{}".format(TMPDB))

Base.metadata.create_all(testengine)
Base.metadata.bind = testengine


def remove_test_db():
    """
    Remove the sqlite file for the test database
    """
    if os.path.exists(TMPDB):
        os.remove(TMPDB)


@contextmanager
def test_session_scope():
    """Provide a transactional scope around a series of operations."""
    db_session = sessionmaker(bind=testengine)
    testsession = db_session()
    try:
        yield testsession
        testsession.commit()
    except Exception:
        testsession.rollback()
        raise
    finally:
        testsession.close()
