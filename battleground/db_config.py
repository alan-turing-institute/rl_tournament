import os

if os.environ["DB_TYPE"] == "sqlite":
    DB_CONNECTION_STRING = "sqlite:////tmp/plarkdata.db"
else:
    DB_CONNECTION_STRING = "postgres://{}:{}@{}/{}".format(
        os.environ["DB_USER"],
        os.environ["DB_PASSWORD"],
        os.environ["DB_URI"],
        os.environ["DB_NAME"],
    )
