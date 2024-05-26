
import socket
import json
import re
import time
from collections import defaultdict
import threading
from time import sleep

from twitchHandler import TwitchHandler

MESSAGE_COUNTS_FILE = "message_counts.json"


try:
    with open(MESSAGE_COUNTS_FILE, "r") as file:
        message_counts = defaultdict(int, json.load(file))
except FileNotFoundError:
    message_counts = defaultdict(int)

def save_message_counts():
    with open(MESSAGE_COUNTS_FILE, "w") as file:
        json.dump(dict(message_counts), file)

def connect_to_twitch_irc():
    irc_socket = socket.socket()

    try:
        irc_socket.connect((server, port))
    except Exception as e:
        print(f"Error connecting to Twitch IRC: {e}")
        return

    token = TwitchHandler.get_oauth_token()
    irc_socket.send(f"PASS oauth:{token}\n".encode("utf-8"))
    irc_socket.send(f"NICK {nickname}\n".encode("utf-8"))
    irc_socket.send(f"JOIN #{channel}\n".encode("utf-8"))

    print('Connected!')
    print(f'Started at {time.strftime("%H:%M")}')
    print('='*20)

    def check_token():
        while True:
            time.sleep(1800)
            if TwitchHandler.token_needs_refreshing():
                new_token = TwitchHandler.load_tokens()['access_token']
                print('<INFO> | Token Refreshed.')
                irc_socket.send(f"PASS oauth:{new_token}\n".encode("utf-8"))

    threading.Thread(target=check_token, daemon=True).start()

    while True:
        try:
            data = irc_socket.recv(1024).decode("utf-8")
        except ConnectionResetError:
            print('<ERROR> | Connection to Twitch IRC reset.')
            break
        except Exception as e:
            print(f"<ERROR> | {e}")
            break

        if not data:
            print('No Data, restarting connection')
            irc_socket.detach()
            irc_socket.close()
            sleep(5)
            connect_to_twitch_irc()

        match = re.match(r":([^!]+)![^ ]+ PRIVMSG #[^ ]+ :(.+)", data)
        if match:
            username = match.group(1)
            message = match.group(2)
            message_counts[username] += 1
            save_message_counts()

            print(f'{username} ({message_counts[username]}): {message}')

    irc_socket.close()
            

if __name__ == "__main__":
    server = "irc.chat.twitch.tv"
    port = 6667
    nickname = "polishdogge"
    channel = "polishdogge"
    connect_to_twitch_irc()