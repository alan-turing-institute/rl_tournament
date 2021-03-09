# API endpoints for querying the Plark tournament DB

Note that all the endpoints below follow the base URL, which would be:
```
localhost:5001
```
if running on your local machine, or something like:
```
https://<webapp_name>.azurewebsites.net
```
if deploying as an Azure web app.

## Endpoints:

### ```/tournaments```
lists all the tournaments, returns:
```
[ {"tournament_id": <id:int>, "tournament_time": <time:str>}, ... ]
```

### ```/tournaments/<tourn_id>```
info on tournament with id <tourn_id>, returns:
```
{
  "tournament_id": <id:int>,
  "tournament_time": <time:str>,
  "panther_agents": [<agent_name>:str, ...],
  "pelican_agents": [<agent_name>:str, ...],
  "matches": [<match_id>:int, ...]
}
```

### ```/matches/<match_id>```
info on match with id <match_id>, returns:
```
{
  "match_id": <id:int>,
  "match_time": <time:str>,
  "panther": <agent_name>:str,
  "pelican": <agent_name>:str,
  "panther_score": <score>:int,
  "pelican_score": <score>:int,
  "winner": <agent_name>:str,
  "logfile": <log_url>:str,
  "games": [<game_id>:int, ...]
}
```

### ```/games/<games_id>```
info on game with id <game_id>, returns:
```
{
  "game_id": <id:int>,
  "game_time": <time:str>,
  "panther": <agent_name>:str,
  "pelican": <agent_name>:str,
  "num_turns": <num_turns>:int,
  "result_code": <code>:str,
  "winner": <agent_type>:str,
  "video": <video_url>:str
}
```

### ```/teams```
list of all teams, returns:
```
[ <team_name>:str, ... ]
```

### ```/agents/<team_name>```
list of all agents for a given team, returns:
```
[ <agent_name>:str, ... ]
```

### ```/pelicans/<tournament_id>```
list of all pelican agents for a given tournament_id, returns
```
[ <agent_name>:str, ... ]
```

### ```/panthers/<tournament_id>```
list of all pelican agents for a given tournament_id, returns:
```
[ <agent_name>:str, ... ]
```
