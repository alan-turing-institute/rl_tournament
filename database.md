## Setting up a postgres database for Plark tournament.

For this tournament we are using Microsoft Database for PostgresSQL on Azure.
See [here](https://docs.microsoft.com/en-us/azure/postgresql/quickstart-create-server-database-portal)  for a quickstart guide on setting this up.
We use a Basic Single server as the storage and computing needs are pretty minimal.

Note that if you want to run from a machine that is not in Azure, you need to follow the "Configure a firewall rule" step to be able to connect to the server from your machine.

You should also follow the steps where you connect to your server via `psql` and create a database.  You might want to create two, e.g. `test` and `tournament`.

### Setting environment variables

As mentioned in [README.md] you should copy the file `.env_template` to `.env` and fill out the fields there.  If you are using Microsoft Database for PostgresSQL, the values to put in the file are:
```
DB_TYPE=postgres
DB_USER=  _Admin username from the 'Overview' page on the [Azure portal](https://portal.azure.com)_
DB_PASSWORD= _the strong random password you created for the admin user_
DB_URI= _'Server name' from the 'Overview' page on the [Azure portal](https://portal.azure.com)_
DB_NAME= _the name of the database you created in the step above via psql_.


### Testing

You can quickly check whether your database connection is working by creating a dummy Team in the database:
```
python
>>> from battleground.schema import session, Team
>>> t = Team()
>>> t.team_name = "TestTeam"
>>> t.team_members = "no-one"
>>> session.add(t)
>>> session.commit()
```
If this works with no errors then everything should be setup correctly.
