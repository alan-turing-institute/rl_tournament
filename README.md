# Reinforcement Learning Tournament

This repository contains code to allow reinforcement learning agents to run the "Hunting the Plark" game in a tournament environment.

The documentation here is aimed at participants in the Reinforcement Learning Data Study Group.  
Developers of this package can find documentation [here](developers.md).

# How to participate in the Tournament

### Before we get started...

Some warnings:

:warning: This tournament environment has been put together in a short space of time and is still undergoing development. Please don't do weird things to crash it!

:warning: Please don't mine bitcoins inside the agents!  Any match taking too long to complete will be automatically killed.

## Computational resources

Teams will be given access to temporary Ubuntu virtual machines (VMs) on Microsoft Azure, which they can use to develop and train their agents. By default each team will be given access to one VM, however, if your team would like to get access to a more powerful or a different type of VM (e.g. VM with a GPU), please get in touch with your facilitator. Please bear in mind that we have a limited amount of cloud computing resources that were provided by The Turing.

### :key: Accessing your team's VM(s)

In order to get access to your VM please contact your team facilitator. You will be asked to provide a public ssh key which will be then used to authenticate and authorise your connection to your team's VMs. 

The facilitator will provide you with an IP address and login name, which then can be used to ssh to your team's VM(s).

> If you are not familiar with the public key cryptography, we would recommend you to consult this [wiki page](https://en.wikipedia.org/wiki/Public-key_cryptography).

### :cloud: Set-up on the VM(s)

It is not possible for us to install all possible software and/or packages that the teams might use, therefore we kept the set up minimal and give the participants admins rights to the VMs so that they can configure them as they see fit.

- The VMs will have preinstalled
  - Docker

### :computer: Local development

Participants are free to develop and train agents on any platform that they see fit. However, they must be able to submit a valid docker image in order to participate in the tournament.

## PlarkAI source code

The source code can be found [here](https://github.com/alan-turing-institute/plark_ai_public). This is a slightly modified version of “The hunting of the PLARK” Artificial Intelligence (AI) testbed that has been developed by Montvieux. The changes are minimal - only to wrap agents into containers that can be used in the tournaments.

When developing agents we recommend creating a fork of the source code and using version control. If needed, facilitators will create GitHub repositories for your team under the Alan Turing Institute account.

## :pencil: How to develop and train PlarkAI

Please follow Montvieux instructions on how to develop and train your agents. Instructions can be found [here](https://github.com/alan-turing-institute/plark_ai_public/blob/master/Documentation/Hunting_The_Plark.pdf)

## :baseball: The Tournament

Tournaments will be organised daily in the evenings on every workday from the 5th to the 12th March 2021, by an automatic process. The results will be given in a form of a table for each tournament day.

## :satellite: Submitting agent(s) to the tournament

In order to submit agents to the tournament, each team needs to prepare them as Docker containers and push them to the tournament's container registry. We have prepared helper routines (Unix/Mac) which you might want to use.

Before the event, each team will be given their private login credentials to a private container repository. Check with your facilitator if you haven't received them.

You should expect to receive your team's `token_name` and `token_value`.

### Where to put your agent

- In order to put your agent into a Docker container, it should be in a subdirectory of your team's `plark_ai_public` repository's main directory.
- You can put your agents wherever you like within the `plark_ai_public` directory structure, but panther agents should be in a subdirectory called `panther`, and similarly for `pelican` - i.e. the paths would be:
``/path/to/plark_ai_public/some/other/directories/panther/directory_containing_panther_agent``
``/path/to/plark_ai_public/some/other/directories/pelican/directory_containing_pelican_agent``
- Then, you need to set the variable `AGENTS_PATH` in the file `plark_ai_public/Combatant/combatant.py` to point to the directory _one level higher_ than the ``panther`` or ``pelican`` directories.   
- **The start of `AGENTS_PATH` should always be ``/plark_ai_public``** (this is how the directory will be mounted on the docker container).
- So, in the example above, you would set
``AGENTS_PATH = /plark_ai_public/some/other/directories/``

Note, if you want to build the image using one of the example agents, you will need to pull with git large file storage: 

`git lfs pull`

This may require you to install:

`sudo apt-get install git-lfs`

### Building a Docker image with your agent

- In the terminal window navigate to your team's `plark_ai_public` repository's main directory.
- `docker build -t turingrldsg.azurecr.io/<<TEAM_ID>>:<<tag>> -f Combatant/Dockerfile .`

  - Here `<<TEAM_ID>>` is your team's name and `<<tag>>` is the tag which should reflect the agent type and its version.

  - If you are submitting a PELICAN agent, make sure that the docker image tag starts with `pelican_`, e.g. `pelican_latest`. Similarly, if you are submitting a PANTHER agent, make sure that the docker image tag starts with `panther_`, e.g. `panther_latest`.

  - It is important to keep track of the tags being used by the team. As you will see in the next step, each team can register multiple agents for each daily tournament. However, we would prefer to keep this number to be <= 3 for each category, in order to ensure that all matches finish on time.
  - **Important**  - for technical reasons, please make your docker tags lower-case only.

  > If you are using Unix/Mac, you might want to use the helper functions `make pelican_build` or `make panther_build` but make sure that you have the `RL_TEAM_ID` environmental variable set as your team's name. If you are not sure what it should be, please check with your facilitator. The format is "team_X" where X is your teams number, for example "team_1", "team_2", etc.

- Make sure that you don't receive any errors. If you received errors, it is a good indication that your Docker container is not built correctly.

### Testing the Docker image with your agent

- In the terminal window navigate to your the `plark_ai_public/` directory (the main directory of your team's fork of the repository), and run the following command to test your agent's docker image: 

- `docker run turingrldsg.azurecr.io/<<TEAM_ID>>:<<tag>> Combatant/tests/test_panther.sh`

- `docker run turingrldsg.azurecr.io/<<TEAM_ID>>:<<tag>> Combatant/tests/test_pelican.sh`

  - Here `<<TEAM_ID>>` is your team's name and `<<tag>>` is the tag which should reflect the agent type and its version, e.g. "pelican_latest".
    
    > The format for `<<TEAM_ID>>` is "team_X" where X is your teams number, for example "team_1", "team_2", etc. If you are not sure what it should be, please check with your facilitator.

- Make sure that you don't receive any errors. If you received errors, it is a good indication that your Docker container is not built correctly.  Please refer to the "Building a docker image with your agent" section above, and make sure you have followed all the instructions carefully.

> If you are using Unix/Mac, you might want to use the helper functions `make pelican_test` or `make panther_test`.  Again, run these from the `plark_ai_public/` directory (the main directory of your team's fork of the repository). If using these commands, make sure that you have the `RL_TEAM_ID` environmental variable set as your team's name. If you are not sure what it should be, please check with your facilitator. The format is "team_X" where X is your teams number, for example "team_1", "team_2", etc.

### Uploading docker images for the tournament

- In the terminal window navigate to your team's `plark_ai_public` repository's main directory 

- Make sure that you have logged in with the provided container registry credentials:

  - `docker login turingrldsg.azurecr.io -u <<token_name>> -p <<token_value>>`

    - Here `<<token_name>>` and `<<token_value>>` are your team's `token_name` and `token_value`.

    > If you are using Unix/Mac, you might want to utilise the helper function `make login` but make sure that you have `RL_TOKEN_NAME` and `RL_TOKEN` environmental variables set as your team's `token_name` and `token_value` respectively.

- Push the image to the container registry

  - `docker push turingrldsg.azurecr.io/<<TEAM_ID>>:<<tag>>`

    - Here `<<TEAM_ID>>` is your team's name and `<<tag>>` is the tag which should reflect the agent type and its version. The format for `<<TEAM_ID>>` is "team_X" where X is your teams number, for example "team_1", "team_2", etc. If you are not sure what it should be, please check with your facilitator.

    - For example, team_test would submit their panther agent using the following command `docker push turingrldsg.azurecr.io/team_test:panther_latest`

    > Again, if you are using Unix/Mac, you might want to use the helper functions `make pelican_push` or `make panther_push` but make sure that you have the `RL_TEAM_ID` environmental variable set as your team's name. If you are not sure what it should be, please check with your facilitator. The format is "team_X" where X is your teams number, for example "team_1", "team_2", etc.


### Registering docker images for the tournament

* Every team will have a corresponding .txt file in the [teams](teams) directory of this repository.  
* Teams can register their agents each day of the challenge by adding their image tags in this file. 
   - Please check [team_test.txt](teams/team_test.txt) for an example.
* Unregistered agents (tags) will not be included in the daily tournaments.




