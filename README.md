# Slack IncidentBot

Slack bot to report incidents

## Prerequisites

- Python 3.7+
- Docker (optional)

## How to setup and run

### Running with python

To run this app inside execute these commands in order:

```shell

# create a virtual environment (recommended)
python -m venv venv

# activate virtual environment
source venv/bin/activate

# install dependencies
pip install --upgrade pip && pip install requirements.txt

# run
SLACK_BOT_TOKEN=xoxb-4928XXXXXX-XXXXXX-XXXXXXXXXXXXXX python main.py

```

### Running inside a Docker container

To run this app inside a docker container just execute these commands in order:

```shell

# Build image
docker build -t slackbot . 

# Run container
docker run -p 5001:5001 --name -e SLACK_BOT_TOKEN=xoxb-4928XXXXXX-XXXXXX-XXXXXXXXXXXXXX slack slackbot

```
---
## Features

- [x] 1. Listen to the messages starting with "/incident".
- [x] 2. When the bot receives a message starting with "/incident", parse the message to extract the incident details.
- [x] 3. Use the Slack API to create a new channel with a name in the format "yyyy_mm_dd_'message'".
- [x] 4. Invite the groups "incident_TF" and "netops_shiftengs" to the new channel.
- [x] 5. Post the incident details in the "downtime" channel with the content described.
"Dear team, We are currently experiencing an issue with: 'Dashboard is down'
Our engineers are currently investigating the issue.
Detailed investigation can be followed at "name of the channel"
- [x] 6. Search for all archived incidents channels names with "extracted message text" in slack and send the name of them as a message in the channel as follows
"I have found possible previous similar incidents: 'name of the archived channels'"
