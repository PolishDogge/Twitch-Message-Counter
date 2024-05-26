import webbrowser
import json
import requests
from time import time

#################
TOKEN_FILE = "oauth_tokens.json"
client_id = ""
client_secret = ""
redirect_uri = "http://localhost"
#################

class TwitchHandler:
    global client_id, client_secret, redirect_uri
    @staticmethod
    def save_tokens(tokens):
        with open(TOKEN_FILE, "w") as file:
            json.dump(tokens, file)

    @staticmethod
    def load_tokens():
        try:
            with open(TOKEN_FILE, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return None

    @staticmethod
    def token_needs_refreshing():
        tempfileread = TwitchHandler.load_tokens()
        if tempfileread and "expires_at" in tempfileread and time() >= tempfileread["expires_at"]:
            refreshed_tokens = TwitchHandler.refresh_token(tempfileread["refresh_token"])
            if refreshed_tokens:
                TwitchHandler.save_tokens(refreshed_tokens)
                return True
        return False

    @staticmethod
    def get_oauth_token():
        saved_tokens = TwitchHandler.load_tokens()
        if saved_tokens and "access_token" in saved_tokens and "refresh_token" in saved_tokens:
            if not TwitchHandler.token_needs_refreshing():
                return saved_tokens["access_token"]

            tokens = TwitchHandler.refresh_token(saved_tokens["refresh_token"])
            if tokens:
                return tokens["access_token"]
        else:
            TwitchHandler.generate_new_tokens()

    @staticmethod
    def generate_new_tokens():

        auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=chat:read&force_verify=true"
        print(auth_url)
        webbrowser.open(auth_url)

        print('After giving access to your app, you will get a code in the link. Example: http://localhost/wGzjf09wSgbjsBM29z << {this is the code}')
        authorization_code = input("Enter the authorization code from the URL: ")

        token_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}",
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{redirect_uri}",
        }

        response = requests.post(token_url, params=params)
        data = response.json()

        if "access_token" in data:
            tokens = {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_at": time() + data["expires_in"] - 300,
            }
            TwitchHandler.save_tokens(tokens)
            return tokens["access_token"]
        else:
            print("Failed to get OAuth token.")
            return None

    @staticmethod
    def refresh_token(refresh_token):
        print('Refreshing token.')
        auth_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(auth_url, params=params)
        data = response.json()

        if "access_token" in data:
            tokens = {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": time() + data["expires_in"] - 600,
            }
            return tokens
        else:
            print("Failed to refresh token.")
            print(data)
            return None