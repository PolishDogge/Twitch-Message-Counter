import webbrowser
import json
import requests
from time import time

#################
TOKEN_FILE = 'oauth_tokens.json'
client_id = ""
client_secret = ""
redirect_uri = "http://localhost"
#################

class TwitchHandler:
    global client_id, client_secret, redirect_uri
    # Save the token for later use
    def save_tokens(tokens):
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, TOKEN_FILE)

    def load_tokens():
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        
    # Check if the token needs refreshing 
    def token_needs_refreshing() -> bool:
        tempfileread = TwitchHandler.load_tokens()
        if tempfileread and "expires_at" in tempfileread and time() >= tempfileread["expires_at"]:
            refreshed_tokens = TwitchHandler.refresh_token(tempfileread["refresh_token"])
            if refreshed_tokens:
                TwitchHandler.save_tokens(refreshed_tokens)
                return True
        return False
    
    # Get a new token
    def get_oauth_token() -> str:
        saved_tokens = TwitchHandler.load_tokens()
        if saved_tokens and "access_token" in saved_tokens and "refresh_token" in saved_tokens:
            if not TwitchHandler.token_needs_refreshing():
                return saved_tokens["access_token"]

            tokens = TwitchHandler.refresh_token(saved_tokens["refresh_token"])
            if tokens:
                return tokens["access_token"]
        else:
            TwitchHandler.generate_new_tokens()

    def generate_new_tokens():
        """
        Get the first token if not given previously
        """
        auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=chat:read&force_verify=true"
        print(auth_url)
        webbrowser.open(auth_url)

        print('After giving access to your app, you will get a code in the link. Example: http://localhost/wGzjf09wSgbjsBM29z << {this is the code}\n')
        authorization_code = input("Enter the authorization code from the URL: ")

        token_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}",
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{redirect_uri}",
        }
        # Get and parse response
        response = requests.post(token_url, params=params)
        data = response.json()

        if "access_token" in data:
            tokens = {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_at": time() + data["expires_in"] - 300,
            } # Remove 10 minutes from the expires at
            TwitchHandler.save_tokens(tokens)
            return tokens["access_token"]
        else:
            print("Failed to get OAuth token.")
            return None
        
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
            } # Removes 10 minutes from the token to make sure that it checks it BEFORE it expires
            return tokens
        else:
            print("Failed to refresh token.")
            print(data)
            return None
    
    def check_twitch(name) -> bool:
        """
        A way of checking if a channel is live without asking the API
        """
        currently_live = []
        try:
            for i in range(len(name)):
                    contents = requests.get('https://www.twitch.tv/' +name[i]).content.decode('utf-8')
                    if 'isLiveBroadcast' in contents: 
                        return True # Cry about it
                    else:
                        return False
        except Exception as e:
            print(f'Exception checking if live {e}')
    
    def get_user_info(username) -> dict:
        """
        Get information about the given user

        id, login, display_name, type, broadcaster_type, description, profile_image_url, view_count, created_at
        """
        token = TwitchHandler.get_oauth_token()
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }
        url = f'https://api.twitch.tv/helix/users?login={username}'
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            return data['data'][0]
        else:
            print("User not found or API request failed.")
            return None
    
    def get_stream_schedule(user) -> dict:
        """
        Get users stream scheadule
        """
        token = TwitchHandler.get_oauth_token()
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }
        url = f'https://api.twitch.tv/helix/schedule?broadcaster_id={user}'
        response = requests.get(url, headers=headers)
        data = response.json()

        if 'data' in data:
            return data['data']
        else:
            print("Failed to fetch stream schedule.")
            return None
    
    def get_stream_info(user) -> dict:
        """
        Get information about the stream

        user name, game name, title, viewer_count, started_at, language, thumbnail_url
        """
        token = TwitchHandler.get_oauth_token()
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }
        url = f'https://api.twitch.tv/helix/streams?user_login={user}'
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            stream_info = data['data'][0]
            return {
                'user_name': stream_info['user_name'],
                'game_name': stream_info['game_name'],
                'title': stream_info['title'],
                'viewer_count': stream_info['viewer_count'],
                'started_at': stream_info['started_at'],
                'language': stream_info['language'],
                'thumbnail_url': stream_info['thumbnail_url']
            }
        else:
            print("Stream not found or API request failed.")
            return None