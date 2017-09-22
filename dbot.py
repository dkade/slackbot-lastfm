import os
import time
from slackclient import SlackClient
from bs4 import BeautifulSoup,Tag
from helpers.config import Config
import requests
import pickle

# filename for user list
FILENAME="userlist"


BOT_ID = Config.get('global', 'bot_id')

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"
COMMAND_CHANNEL= Config.get('global', 'channel') #channel where the bot will serve commands TODO: block to channel
MASTER= Config.get('global', 'owner') #IF you want to use a master user for special commands TODO

# instantiate Slack & Twilio clients
slack_client = SlackClient(Config.get('global', 'bot_key'))
lastfm_list = {}

def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

# try to open the file, check for it
try:
    lastfm_list = load_obj(FILENAME)
    pass
except Exception as e:
    print ("Filename doesn't exist!")
    pass

def getSong(username):
    url = "http://last.fm/user/" + username
    print(url)
    result = requests.get(url)
    soup = BeautifulSoup(result.content, "lxml")
    current_play = soup.find("tr", "now-scrobbling")
    if current_play:
        song = "is listening to: :musical_note: *" + current_play.find("td", "chartlist-name").text.strip().replace("\n", "").replace("\u2014", "-") + "*"
        return song
    else:
        return "*hasn't scrobled anything in a while!*"

def getRandomBand():
  url = 'https://www.metal-archives.com/band/random'
  bstats = None
  try:
    url_next=requests.head(url, timeout=100).headers.get('location', url)
    band_page = requests.get(url_next)
    soup = BeautifulSoup(band_page.content, "html.parser")
    band_name = soup.find("h1", "band_name").a.text
    bstats = soup.select("div[id=band_stats]")
    stats=[]
  except Exception as e:
      print("Something went very wong")
      print(e)
  if bstats is None:
      return "Something is fucky with metal-archives!!!"
  for line in bstats:
    for child in line.find_all_next("dl"):
      for item in child.children:
        if isinstance(item, Tag):
          stats.append(item.text)
  dict_stats = dict(zip(stats[0::2], stats[1::2]))
  return band_name + " ( " + url_next + " ) " + dict_stats['Genre:'] + ' from ' + dict_stats['Country of origin:'] + ' ('+dict_stats['Status:']+')'



# Example of a JSON received by the bot
# [{'team': 'T625JDJ3V', 'type': 'message', 'channel': 'C6K3HPFQ1', 'user': 'U6S7R20M8', 'text': '.np', 'ts': '1502197658.841748', 'source_team': 'T62AJ6J3V'}]

def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = ""
    if command.startswith(".np", 0):
        if user in lastfm_list:
            print (lastfm_list[user])
            print("Scrubing...")
            print(getSong(lastfm_list[user]))
            response = "<@" + user + "> " + getSong(lastfm_list[user])
        else:
            response = "<@" + user +"> to set you last fm user, type: .set <username>"
    elif command.startswith(".set" , 0):
        lastfm_list[user] = command.split(" ")[1]
        save_obj(lastfm_list, FILENAME)
        response = "<@" + user +"> last fm user set to: " + lastfm_list[user]
        #response = "Sure...write some more code then I can do that!"
    elif command.startswith(".random" , 0):
        response = getRandomBand()
    else:
        response = "<@" + user +"> available commands: *.np* and *.set <username>*"
    if response:
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
  """
      The Slack Real Time Messaging API is an events firehose.
      this parsing function returns None unless a message is
      directed at the Bot, based on its ID.
  """
  output_list = slack_rtm_output
  # print(output_list)
  if output_list and len(output_list) > 0:
      for output in output_list:
          if output and 'text' in output and output['text'].startswith('.', 0): # and AT_BOT in output['text']:
              # print(output)
              # print(output['text'])
              # return text after the @ mention, whitespace removed
              # return output['text'].split(AT_BOT)[1].strip().lower(), \
              # output['channel']
              return output['text'], output['channel'], output['user']
  return None, None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
