import os
import logging
from openai import OpenAI
import requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

print("Running")

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
OAI_BASE_URL = os.getenv("OAI_BASE_URL")
OAI_KEY = os.getenv("OAI_KEY")
MODERATION_BASE_URL = os.getenv("MODERATION_BASE_URL")
MODERATION_KEY = os.getenv("MODERATION_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

# Constants
PADLET_URL = "https://padlet.com/vvvrrrrvrr/alex-s-ideas-and-things-s4nym2jtp3dthauj"
ALEX_USER_ID = "U09PHG7RLGG"
HTTP_TIMEOUT = 10  # seconds
MAX_CONVERSATION_HISTORY = 10

txt_client = OpenAI(
   base_url = OAI_BASE_URL,
   api_key = OAI_KEY
)

mod_client = OpenAI(
   base_url = MODERATION_BASE_URL,
   api_key = MODERATION_KEY
)

app = App(token=SLACK_BOT_TOKEN)

# Cache bot user ID to avoid repeated API calls
_bot_user_id_cache = None

def get_bot_user_id(client):
    """Get bot user ID with caching to avoid repeated API calls."""
    global _bot_user_id_cache
    if _bot_user_id_cache is None:
        try:
            bot_info = client.auth_test()
            _bot_user_id_cache = bot_info["user_id"]
        except Exception as e:
            logger.error(f"Failed to get bot user ID: {e}")
            # Return None to allow the caller to handle the error
            return None
    return _bot_user_id_cache

@app.event("member_joined_channel")
def welcome_to_the_channel(event, say, client):
    user_id = event["user"]
    bot_user_id = get_bot_user_id(client)
    
    # If we can't get bot user ID or if the user is the bot, skip
    if bot_user_id is None or user_id == bot_user_id:
        return
    blocks = [
        
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"Hi, <@{user_id}> :aga:! Welcome to Alex's channel! Plz enjoy your stay! :meow_code:"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*:pf: WAT IS A PADLET BRO!!?!?*\nits like a trello board but its cool and customizable.......like really..(i havent tried it..)"
			}
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": "P.S: i dont know what is a padlet and it looks like a cool trello alternative"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "OPEN THE PADLET!! :rac_wtf:",
						"emoji": True
					},
					"url": PADLET_URL,
					"action_id": "visit_padlet"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Summon Alex",
						"emoji": True
					},
					"value": "ping_alex",
					"action_id": "summon_ts_dude",
					"style": "primary"
				}
			]
		}
	]


    say(text=f"Hi, <@{user_id}>!", blocks=blocks)

@app.action("summon_ts_dude")
def handle_ping_alex(ack, body, client):
    ack()

    clicker = body["user"]["id"]
    channel_id = body["channel"]["id"]
    
    client.chat_postMessage(
        channel = channel_id,
        text=f"<@{ALEX_USER_ID}>! You have been summoned by <@{clicker}>"
    )

@app.command("/padlet")
def handle_padlet_cmd(ack, respond, command):
    ack()
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here is the Padlet URL! :aga:"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "OPEN THE PADLET!! :rac_wtf:",
                        "emoji": True
                    },
                    "url": PADLET_URL,
                    "action_id": "visit_padlet_cmd"
                }
            ]
        }
    ]
    
    respond(blocks=blocks)

@app.command("/factoftheday")
def fact_of_the_day(ack, say, command, event, logger):
    ack()
    try:
        response = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/today", timeout=HTTP_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch fact of the day: {e}")
        say({
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "Sorry, I couldn't fetch a fact right now. Please try again later.",
                        "emoji": True
                    }
                }
            ]
        })
        return

    data = response.json()
    fact = data.get('text', 'No fact available')

    say(
        {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "Here is your fact for today.",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": f"{fact}",
                        "emoji": True
                    }
                }
            ]
        }
    )

@app.event("app_mention")
def ai_mention(client, event, say, logger):
    user_msg = event['text']
    thread_ts = event.get("thread_ts", event["ts"])
    channel_id = event["channel"]
    message_ts = event["ts"]
    
    try:
        client.reactions_add(
            channel=channel_id,
            timestamp=message_ts,
            name="thought_balloon"
        )
    except Exception as e:
        logger.warning(f"Unable to add reaction: {e}")
    
    try:
        moderation = mod_client.moderations.create(input=user_msg)
        if moderation.results[0].flagged:
            say(
                text="I am unable to generate a response because your message contains flagged content.",
                thread_ts=thread_ts
            )
            return
        
        mem = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=MAX_CONVERSATION_HISTORY
        )
        mem_data = mem['messages']
        
        coolest_prompt= """You are to adopt the persona of a detached, "chronically online" internet user. Adhere strictly to the following formatting and stylistic rules:

1.  **Lowercase Only:** Never use capital letters. Everything must be in lowercase.
2.  **No Emojis:** Strictly forbidden. Do not use emoticons :) or emojis.
3.  **Sentence Structure:** Keep responses extremely short, choppy, and fragmented. Avoid long paragraphs.
4.  **Slang Usage:** Use internet slang frequently but naturally (e.g., fr, ngl, tbh, rn, bruh, mid, cap, bet, vibe, idc).
5.  **Tone:** Apathetic, chill, and slightly sarcastic. Do not be overly polite or helpful. Act like you are replying to a text message or a Discord DM.
6.  **Punctuation:** Use minimal punctuation. Stop using periods at the end of sentences. Use commas sparingly.

If the user asks a complex question, give a correct answer but phrase it like it's common knowledge or you can't be bothered to explain the whole thing.
"""
        
        conversation_context = [
            {"role": "system", "content": coolest_prompt}
        ]
        
        for msg in mem_data:
            text = msg.get("text", "")
            if "bot_id" in msg:
                conversation_context.append({"role": "assistant", "content": text})
            else:
                conversation_context.append({"role": "user", "content": text})
        
        response = txt_client.chat.completions.create(
            model=LLM_MODEL,
            messages=conversation_context,
            max_tokens=500
        )
        
        ai_reply = response.choices[0].message.content
        say(text=ai_reply, thread_ts=thread_ts)
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        say(text=f"Oops! Unable to get a response from OpenAI.", thread_ts=thread_ts)
    
    finally:
        try:
            client.reactions_remove(
                channel=channel_id,
                timestamp=message_ts,
                name="thought_balloon"
            )
        except Exception as e:
            logger.warning(f"Unable to remove reaction: {e}")


# the fire starter
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()