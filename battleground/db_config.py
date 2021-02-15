import os

if os.environ["PlarkDBType"] == "sqlite":
    DB_CONNECTION_STRING = "sqlite:////tmp/plarkdata.db"
else:
    DB_CONNECTION_STRING = "postgres://{}:{}@{}/{}".format(
        os.environ["PlarkDBUser"],
        os.environ["PlarkDBPassword"],
        os.environ["PlarkDBUri"],
        os.environ["PlarkDBName"]
    )
