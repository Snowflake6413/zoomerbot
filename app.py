import os
import logging
from openai import OpenAI
import requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

print("Running")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
OAI_BASE_URL = os.getenv("OAI_BASE_URL")
OAI_KEY = os.getenv("OAI_KEY")
MODERATION_BASE_URL = os.getenv("MODERATION_BASE_URL")
MODERATION_KEY = os.getenv("MODERATION_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

txt_client = OpenAI(
   base_url = OAI_BASE_URL,
   api_key = OAI_KEY
)

mod_client = OpenAI(
   base_url = MODERATION_BASE_URL,
   api_key = MODERATION_KEY
)

app = App(token=SLACK_BOT_TOKEN)

@app.event("member_joined_channel")
def welcome_to_the_channel(event, say, client):
    user_id = event["user"]
    padlet_url = "https://padlet.com/vvvrrrrvrr/alex-s-ideas-and-things-s4nym2jtp3dthauj"
    bot_info = client.auth_test()
    bot_user_id = bot_info["user_id"]
    
    if user_id == bot_user_id:
        return
    blocks = [
        
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"Hi, <@{user_id}> :aga:! Welcome to Alex's channel! Plz enjoy your stay! :meow_code: This Padlet is like a kanban board. It's like a Todo list!"
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
					"url": padlet_url,
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
    
    alex_user_id = "U09PHG7RLGG"
    
    client.chat_postMessage(
        channel = channel_id,
        text=f"<@{alex_user_id}>! You have been summoned by <@{clicker}>"
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
                    "url": "https://padlet.com/vvvrrrrvrr/alex-s-ideas-and-things-s4nym2jtp3dthauj",
                    "action_id": "visit_padlet_cmd"
                }
            ]
        }
    ]
 
 respond(blocks=blocks)

@app.command("/factoftheday")
def fact_of_the_day(ack, say, command):
 ack()
 response = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/today")

 if response.status_code == 200:
  data = response.json()
 fact = data['text']

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
    logger.info("hello steven")
    print("hi steven")
    logger.info(event)
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
        print("Unable to add reaction")
    
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
            limit=10
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
        say(text=f"Oops! Unable to get a response from OpenAI. {e}", thread_ts=thread_ts)
    
    finally:
        try:
            client.reactions_remove(
                channel=channel_id,
                timestamp=message_ts,
                name="thought_balloon"
            )
        except Exception as e:
            print("Unable to remove reaction")


# the fire starter
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()