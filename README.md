# Twitch-Message-Counter
Counts the messages from a specified twitch chat. 

# Usage
It uses the [PythonTwitchOAuth](https://github.com/PolishDogge/PythonTwitchOAuth), which has instructions on how to set it up.

Afterwards change the `channel = "CHANNEL"` to the channel you'd like to keep track of.

The amount of chat messages is kept in `message_counts.json`

# Requirements
* Python 3.7+
* `socket` module
* `re` module
* `time` module
* `threading` module
* `collections` module
* `json module`
