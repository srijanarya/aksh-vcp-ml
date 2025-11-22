import os
import requests
import json

# Load from .env.bot
env_file = "/home/ubuntu/vcp/.env.bot"
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if 'TELEGRAM_BOT_TOKEN' in line:
                token = line.split('=')[1].strip()
                print(f"Found token: {token[:5]}...")
                
                # Get updates
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                try:
                    response = requests.get(url, timeout=10)
                    data = response.json()
                    if data.get('ok'):
                        results = data.get('result', [])
                        if results:
                            print(f"\nFound {len(results)} updates.")
                            last_chat = results[-1]['message']['chat']
                            print(f"Last chat ID: {last_chat['id']}")
                            print(f"Chat type: {last_chat['type']}")
                            print(f"Chat title: {last_chat.get('title', 'N/A')}")
                        else:
                            print("\nNo updates found. Send a message to the bot to get chat ID.")
                    else:
                        print(f"Error: {data}")
                except Exception as e:
                    print(f"Request failed: {e}")
else:
    print(".env.bot not found")
