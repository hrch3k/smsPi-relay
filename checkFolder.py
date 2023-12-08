#!/usr/bin/python
import requests
import json
import re
import inotify.adapters

# Initialize inotify to watch the folder for changes
i = inotify.adapters.InotifyTree('/var/spool/gammu/inbox/')


# Function to get all messages in inbox and extract the last message
def getInboxLastEntry():
  url = "http://localhost:8080/get.php"
  response = requests.get(url)
  json_data = response.json()
  formatted_json = json.dumps(json_data[-1], indent=4)
  last_entry = json_data[-1]

  message = last_entry["message"]
  sender = last_entry["sender"]


  print(last_entry)
  print(f"Message: {message}")
  print(f"Sender: {sender}")

  # Check for keyword
  if re.search("keyword", message, flags=re.IGNORECASE):
    print("We have correct keyword in the message. Sending response to sender:", sender)
    sendResponse(sender)
  else:
    print("Message does not contain word:")


# Function to send message 
def sendResponse(sender):
  url = "http://localhost:8080/send.php?phone=" + sender + "&text=Response message. You can customize this"
  #json_data = {"key1": "value1", "key2": "value2"}
  #response = requests.post(url, json=json_data)
  response = requests.get(url)
  print(response)

#getInboxLastEntry()


# For every inotify event that occurs in folder check for IN_CLOSE_WRITE event (This event occurs when the file is closed after writing)
for event in i.event_gen(yield_nones=False):
  (_, type_names, path, filename) = event
  #print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format( path, filename, type_names))
  #print(type_names)
  if (type_names == ["IN_CLOSE_WRITE"]):
    print("New message recieved: FILENAME=[{}] EVENT_TYPES={}".format( path, filename, type_names))
    getInboxLastEntry()

