import socket
import json
import re
from time import sleep
from collections import defaultdict
import threading
from time import sleep
from os import path, mkdir

from twitchHandler import TwitchHandler

def save_message_counts(channel, message_counts):
    filename = f"{channel}_messages.json"
    if not path.exists('counts'):
        mkdir('counts')
    with open(f'counts/{filename}', "w") as file:
        json.dump(dict(message_counts), file)

def load_message_counts(channel):
    filename = f"{channel}_messages.json"
    try:
        if not path.exists('counts'):
            mkdir('counts')
        with open(f'counts/{filename}', "r") as file:
            return defaultdict(int, json.load(file))
    except FileNotFoundError:
        return defaultdict(int)

def connect_to_twitch_irc(channel, token):
    irc_socket = socket.socket()
    message_counts = load_message_counts(channel)

    try:
        irc_socket.connect((server, port))
    except Exception as e:
        print(f"Error connecting to Twitch IRC for {channel}: {e}")
        return

    irc_socket.send(f"PASS oauth:{token}\n".encode("utf-8"))
    irc_socket.send(f"NICK {nickname}\n".encode("utf-8"))
    irc_socket.send(f"JOIN #{channel}\n".encode("utf-8"))

    print(f'Connected to @{channel}!')

    def check_token():
        while True:
            sleep(1800)
            if TwitchHandler.token_needs_refreshing():
                new_token = TwitchHandler.load_tokens()['access_token']
                print(f'<INFO> | Token Refreshed for {channel}.')
                irc_socket.send(f"PASS oauth:{new_token}\n".encode("utf-8"))

    threading.Thread(target=check_token, daemon=True).start()

    while True:
        try:
            data = irc_socket.recv(1024).decode("utf-8")
        except ConnectionResetError:
            print(f'<ERROR> | Connection to Twitch IRC reset for {channel}.')
            break
        except Exception as e:
            print(f"<ERROR> | {e} for {channel}")
            break

        if not data:
            print(f'No Data for {channel}, restarting connection')
            irc_socket.close()
            sleep(5)
            connect_to_twitch_irc(channel, token)

        match = re.match(r":([^!]+)![^ ]+ PRIVMSG #[^ ]+ :(.+)", data)
        if match:
            username = match.group(1)
            message = match.group(2)
            message_counts[username] += 1
            save_message_counts(channel, message_counts)

            print(f'{channel} | {username} ({message_counts[username]}): {message}')

    irc_socket.close()

if __name__ == "__main__":
    server = "irc.chat.twitch.tv"
    port = 6667
    nickname = "polishdogge"
    channels = ["polishdogge"]
    token = TwitchHandler.get_oauth_token()
    threads = []
    for channel in channels:
        thread = threading.Thread(target=connect_to_twitch_irc, args=(channel,token,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()