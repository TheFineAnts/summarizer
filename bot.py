from telegram import Bot
from telegram.ext import Updater, CommandHandler
import logging
import schedule
import time
from datetime import datetime, timedelta
import pytz

# Set your bot token and group chat ID
BOT_TOKEN = 'YOUR_BOT_TOKEN'
GROUP_CHAT_ID = 'YOUR_GROUP_CHAT_ID'

# Initialize the bot
bot = Bot(token=BOT_TOKEN)

# Set the timezone for Singapore
sg_timezone = pytz.timezone('Asia/Singapore')

# Function to fetch messages in batches
def fetch_messages(chat_id, limit=5000):
    all_messages = []
    offset_id = 0

    while len(all_messages) < limit:
        # Fetch the next batch of messages
        batch = bot.get_chat_history(chat_id, offset=offset_id, limit=min(100, limit - len(all_messages)))
        
        if not batch:
            break  # Break if no more messages are available

        all_messages.extend(batch)
        offset_id = batch[-1].message_id  # Update the offset to the last message ID for pagination

    return all_messages

# Function to fetch and summarize messages
def summarize_chat():
    try:
        # Fetch up to 5000 messages
        chat_history = fetch_messages(GROUP_CHAT_ID, limit=5000)

        # Initialize summary variables
        summary = "Today's Chat Summary:\n\n"
        users_mentioned = set()

        # Calculate the time window: 18:00 yesterday to 18:00 today
        now = datetime.now(sg_timezone)
        start_time = now.replace(hour=18, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_time = now.replace(hour=18, minute=0, second=0, microsecond=0)

        # Process messages
        for message in chat_history:
            # Check if the message is within the time window (18:00 yesterday to 18:00 today)
            if start_time <= message.date <= end_time:
                text = message.text
                user = message.from_user.first_name

                # Check for keywords or topics
                if "article" in text.lower():
                    summary += f"✍️ {user} discussed article feedback.\n"
                if "event" in text.lower():
                    summary += f"📅 {user} discussed event planning.\n"
                if "Bangkok" in text:
                    summary += f"✈️ {user} discussed the Bangkok trip.\n"
                
                # Add user to mentioned set
                users_mentioned.add(user)

        # Add users mentioned in the summary
        summary += "\nUsers involved in the discussion:\n" + ", ".join(users_mentioned)

        # Send summary to the group
        bot.send_message(chat_id=GROUP_CHAT_ID, text=summary)

    except Exception as e:
        logging.error(f"Error summarizing chat: {e}")

# Function to schedule the bot summary at 6 PM Singapore time
def schedule_daily_summary():
    sg_time = datetime.now(sg_timezone).strftime("%H:%M:%S")
    if sg_time == "18:00:00":  # 6 PM in Singapore time
        summarize_chat()

# Start the bot's daily summary scheduler
schedule.every().day.at("18:00").do(summarize_chat)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
