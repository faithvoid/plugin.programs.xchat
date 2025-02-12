import xbmc
import xbmcgui
import requests
import os
import time
import unicodedata

# Script constants
SCRIPT_NAME = 'xChat'
BASE_URL = 'https://bsky.social/xrpc/'
CHAT_URL = 'https://api.bsky.chat/xrpc/'
CHECK_INTERVAL = 5  # Interval in seconds to check for new messages
LOGIN_FILE = os.path.join(os.path.dirname(__file__), 'login.txt')
MESSAGES_FILE = os.path.join(os.path.dirname(__file__), 'messages.txt')
HANDLES_FILE = os.path.join(os.path.dirname(__file__), 'handles.txt')

# Load login credentials
def load_credentials():
    if os.path.exists(LOGIN_FILE):
        with open(LOGIN_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    return None, None

# Authenticate with BlueSky using app password
def authenticate(username, app_password):
    url = BASE_URL + 'com.atproto.server.createSession'
    data = {
        'identifier': username,
        'password': app_password
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        xbmc.log("{}: Authentication successful".format(SCRIPT_NAME), xbmc.LOGINFO)
        return response.json()
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Authentication failed. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return None

# Fetch conversations from BlueSky
def fetch_conversations(session):
    url = CHAT_URL + 'chat.bsky.convo.listConvos'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        convos = response.json().get('convos', [])
        return convos
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch conversations. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return []

# Fetch messages for a conversation from BlueSky
def fetch_messages(session, convo_id):
    url = CHAT_URL + 'chat.bsky.convo.getMessages'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    params = {
        'convoId': convo_id
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        messages = response.json().get('messages', [])
        
        # Collect all DIDs to fetch profiles in bulk
        dids = {message['sender']['did'] for message in messages if 'sender' in message and 'did' in message['sender']}
        profiles = load_profiles()
        new_profiles = {did: fetch_profile(session, did) for did in dids if did not in profiles}
        profiles.update(new_profiles)
        save_profiles(new_profiles)
        
        # Ensure each message has the sender's handle
        for message in messages:
            if 'sender' in message and 'did' in message['sender']:
                sender_profile = profiles.get(message['sender']['did'], {})
                message['sender']['handle'] = sender_profile.get('handle', 'Unknown')

        # Sanitize message text
        for message in messages:
            if 'text' in message:
                message['text'] = sanitize_text(message['text'])

        return messages
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch messages. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return []

# Fetch profile information from BlueSky
def fetch_profile(session, did):
    url = BASE_URL + 'app.bsky.actor.getProfile'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    params = {
        'actor': did
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch profile. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return {}

# Load profiles from file
def load_profiles():
    if os.path.exists(HANDLES_FILE):
        with open(HANDLES_FILE, 'r') as f:
            return {line.split(",")[0]: {"handle": line.split(",")[1].strip()} for line in f}
    return {}

# Save profiles to file
def save_profiles(profiles):
    with open(HANDLES_FILE, 'a') as f:
        for did, profile in profiles.items():
            f.write("{},{}\n".format(did, profile.get('handle', 'Unknown')))

# Load old message IDs from file
def load_old_message_ids():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# Save new message ID to file
def save_message_id(message_id):
    with open(MESSAGES_FILE, 'a') as f:
        f.write(message_id + '\n')

# Sanitize text by removing non-ASCII characters
def sanitize_text(text):
    return ''.join(char for char in text if ord(char) < 128)

# Main service loop
def main():
    username, app_password = load_credentials()
    if not username or not app_password:
        xbmc.log("{}: Please enter your BlueSky username and app password in login.txt.".format(SCRIPT_NAME), xbmc.LOGERROR)
        return

    session = authenticate(username, app_password)
    if not session:
        return

    old_message_ids = load_old_message_ids()
    user_did = session.get('did')
    while True:
        convos = fetch_conversations(session)
        for convo in convos:
            messages = fetch_messages(session, convo.get('id'))
            for message in messages:
                message_id = message.get('id')
                if message_id not in old_message_ids:
                    # Skip messages sent by the logged-in user
                    if message.get('sender', {}).get('did') == user_did:
                        continue

                    old_message_ids.add(message_id)
                    save_message_id(message_id)
                    user_handle = message.get('sender', {}).get('handle', 'Unknown')
                    text = message.get('text', 'No text')
                    xbmc.executebuiltin('Notification("{0}", "{1}", 5000, "")'.format(user_handle, sanitize_text(text)))
        
        xbmc.sleep(CHECK_INTERVAL * 1000)

if __name__ == '__main__':
    main()
