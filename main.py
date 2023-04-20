import os
import re
import datetime
from flask import Flask, request
from logging.config import dictConfig
from dotenv import dotenv_values
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from difflib import SequenceMatcher

SLACK_BOT_TOKEN=os.environ.get("SLACK_BOT_TOKEN")

assert SLACK_BOT_TOKEN, f"Environemnt variable SLACK_BOT_TOKEN not defined."

client = WebClient(token=SLACK_BOT_TOKEN)

env = dotenv_values(".env")

PORT=env.get("PORT")
RESPONSE_TEMPLATE=env.get("RESPONSE_TEMPLATE")
RESPONSE_LIST_OF_INCIDENTS_TEMPLATE=env.get("RESPONSE_LIST_OF_INCIDENTS_TEMPLATE")
GROUPS_TO_INVITE=env.get("GROUPS_TO_INVITE")
CHANNEL_TO_POST_INCIDENT=env.get("CHANNEL_TO_POST_INCIDENT")
INCIDENT_MAIN_MESSAGE=env.get("INCIDENT_MAIN_MESSAGE")
GENERIC_ERROR_MESSAGE=env.get("GENERIC_ERROR_MESSAGE")

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

def get_date_time():
    now = datetime.datetime.now()
    return now.strftime('%Y_%m_%d')

def get_incident_channel_title(text):
    date=get_date_time()
    snake_title=text.lower().replace(" ","_").replace("-", "_")[:60]
    return f"{date}_{snake_title}"

def post_message_on_downtime_channel(title,new_channel_id):
    app.logger.info(f"Bot trying to join in the channel #{CHANNEL_TO_POST_INCIDENT} ...")
    channels=client.conversations_list().get("channels")
    channel_id=[x for x in channels if x.get("name") == CHANNEL_TO_POST_INCIDENT][0].get("id")
    client.conversations_join(channel=channel_id)
    app.logger.info(f"Bot joined the channel #{CHANNEL_TO_POST_INCIDENT}")
    client.chat_postMessage(channel=f"#{CHANNEL_TO_POST_INCIDENT}", text=RESPONSE_TEMPLATE.format(title,new_channel_id))

def get_list_of_usergroups_to_invite_ids():
    usergroups=client.usergroups_list()
    usergroups_to_invite=[x for x in usergroups.get("usergroups") if x.get("name") in GROUPS_TO_INVITE]
    return [x.get("id") for x in usergroups_to_invite]

def get_list_of_users(usergroup_id):
    return client.usergroups_users_list(usergroup=usergroup_id)

def invite_groups_to_new_channel(channel_id):
    app.logger.info(f"Inviting usergroups {GROUPS_TO_INVITE} to the new incident channel {channel_id}")
    usergroups_ids=get_list_of_usergroups_to_invite_ids()
    for usergroup_id in usergroups_ids:
        users=get_list_of_users(usergroup_id)
        users_ids=[x for x in users.get("users")]
        client.conversations_invite(channel=channel_id,users=users_ids)

def filter_archived_channels(channels):
    return [x for x in channels.get("channels") if x.get("is_archived") == True and re.search('(\d{4}_\d{2}_\d{2}.+)', x.get("name")) is not None]

def remove_stop_words(list):
  stop_words=['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than']
  return [x for x in list if x not in stop_words]  

def remove_empty_string_from_list(list):
  return [x for x in list if x != '']

def tokenize_title(title):
  result=remove_empty_string_from_list(title.split("_"))
  return remove_stop_words(result)

def is_token_present(token,token_list):
  return token in token_list

def filter_similar_titles(title1, title2):
    regex='(\d{4}_\d{2}_\d{2})?(.+)'
    # to get just the string part, without the timestamp
    title1=re.search(regex, title1).group(2)
    title2=re.search(regex, title2).group(2)
    
    #to remove all digits from the remaining part of the title
    title1=re.sub(r'[0-9]', '', title1)
    title2=re.sub(r'[0-9]', '', title2)

    # to split the titles in a list of words
    tokens1=tokenize_title(title1.lower())
    tokens2=tokenize_title(title2.lower())
    #to check if one of the tokenized words is present on the channel title
    result = len([x for x in tokens2 if is_token_present(x,tokens1)]) > 0
    return result

def filter_similar_channels(title, channels):
    return [f'<#{x.get("id")}>' for x in channels if filter_similar_titles(x.get("name"), title)]

def get_similar_archived_channels(incident_channel_name):
    channels=client.conversations_list()
    archived_channels=filter_archived_channels(channels)
    similar=filter_similar_channels(incident_channel_name, archived_channels)
    return similar

def create_incident(text):
    incident_channel_name=get_incident_channel_title(text)
    app.logger.info(f"Incident channel name to be created: {incident_channel_name}")
    channel_response=client.conversations_create(name=incident_channel_name)
    channel_id=channel_response.get("channel").get("id")
    client.chat_postMessage(channel=f"#{incident_channel_name}", text=INCIDENT_MAIN_MESSAGE.format(text))
    app.logger.info(f"Incident channel created: {incident_channel_name} with ID {channel_id}")
    post_message_on_downtime_channel(text, channel_id)
    invite_groups_to_new_channel(channel_id)
    similar=get_similar_archived_channels(incident_channel_name)
    if len(similar) > 0:
        client.chat_postMessage(channel=f"#{incident_channel_name}", text=RESPONSE_LIST_OF_INCIDENTS_TEMPLATE.format(', '.join(similar)))


app = Flask(__name__)

@app.post("/")
def open_incident():
    app.logger.info("Openning a new incident")
    token = request.form.get("token")
    channel_id=request.form.get("channel_id")
    channel_name=request.form.get("channel_name")
    user_name = request.form.get("user_name")
    text = request.form.get("text")
    app.logger.info(f"Arguments: token={token} , channel_name={channel_name}, user_name={user_name}, text='{text}'")

    try:
       create_incident(text)
    except Exception as e:
       if "/incident failed with the error \"dispatch_failed\"" in str(e):
           raise Exception(GENERIC_ERROR_MESSAGE)
       else:
           client.conversations_join(channel=channel_id)
           client.chat_postMessage(channel='#{}'.format(channel_name), text='{}'.format(GENERIC_ERROR_MESSAGE))
    return "Ok", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
