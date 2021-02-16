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

testengine = create_engine("sqlite:///{}/plarktest.db".format(TMPDIR))

Base.metadata.create_all(testengine)
Base.metadata.bind = testengine


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
