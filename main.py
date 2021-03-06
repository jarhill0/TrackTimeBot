import json
import os
from datetime import datetime, timedelta
from sys import argv

import pawt

from secrets import TOKEN

FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
HOURS = ('12 am', '1 am', '2 am', '3 am', '4 am', '5 am', '6 am', '7 am', '8 am', '9 am', '10 am', '11 am',
         '12 pm', '1 pm', '2 pm', '3 pm', '4 pm', '5 pm', '6 pm', '7 pm', '8 pm', '9 pm', '10 pm', '11 pm',)
MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
TODAY = datetime.today().date()
YESTERDAY = TODAY - timedelta(1)
NOW = datetime.now()

tg = pawt.Telegram(TOKEN)
with open(os.path.join(FOLDER_PATH, 'data', 'user_info.json')) as f:
    user_info = json.load(f)
with open(os.path.join(FOLDER_PATH, 'data', 'subscribed.json')) as f:
    subscribed = set(json.load(f))

ME = tg.get_me()


def subscribe(message):
    if message.user.id in subscribed:
        return
    subscribed.add(message.user.id)
    user_info[message.user.id] = [None] * 24
    try:
        message.reply('You have been subscribed.')
    except pawt.APIException:
        # likely blocked
        pass


def unsubscribe(message):
    if message.user.id in subscribed:
        subscribed.remove(message.user.id)
    if message.user.id in user_info.keys():
        del user_info[message.user.id]
    try:
        message.reply('You have been unsubscribed.')
    except pawt.APIException:
        # likely blocked
        pass


def start(message):
    text = (
        "Hi {}. I'm a bot for tracking your time. Send me /subscribe to start.\nI only check my messages once "
        "an hour, so don't be worried if I don't respond immediately.").format(message.user.full_name)
    try:
        message.chat.send_message(text)
    except pawt.APIException:
        # likely blocked
        pass


def help_(message):
    text = ('My commands:\n\n/subscribe: subscribe to messages\n/unsubscribe: unsubscribe from messages'
            "\n/help: view this message\n\nI only check my messages once an hour, so don't be worried if I "
            "don't respond immediately.")
    try:
        message.chat.send_message(text)
    except pawt.APIException:
        # likely blocked
        pass


def next_(message):
    command_count = sum(1 if isinstance(entity, pawt.BotCommand) else 0 for entity in message.entities)
    if command_count != 1:
        response = 'Sorry, /next is only supported when it is the only command in a message.'
        try:
            message.chat.send_message(response)
        except pawt.APIException:
            # likely blocked
            pass
        return

    full_text = message.get_text_content()
    command = [entity for entity in message.entities if isinstance(entity, pawt.BotCommand)][0]
    text_index = command.offset + command.length

    activity_text = full_text[text_index:].strip()
    user = user_info.get(message.chat.id)
    if not user:
        return

    hour = datetime.fromtimestamp(message.date).hour
    if hour == 0:
        # Before the daily action at 12:55am, /next will accidentally affect the previous day. No can do.
        return

    user[hour] = activity_text


COMMAND_MAP = {'/subscribe': subscribe, '/unsubscribe': unsubscribe, '/start': start, '/help': help_,
               '/next': next_}


def process_updates():
    updates = sorted(tg.get_updates(timeout=0), key=lambda update: update.id)
    if not updates:
        return
    update_id = updates[-1].id + 1
    tg.get_updates(offset=update_id, timeout=0)  # to mark this update as read.

    for u in updates:
        if u.content_type not in ('message', 'edited_message'):
            continue
        m = u.content
        if not m.text:
            continue
        if m.entities:
            for entity in m.entities:
                if not isinstance(entity, pawt.BotCommand):
                    continue
                command_handler = COMMAND_MAP.get(entity.command)
                if command_handler:
                    command_handler(m)
        else:
            if not m.reply_to_message:
                continue
            if m.reply_to_message.user != ME:
                continue
            reply_date = datetime.fromtimestamp(m.reply_to_message.date).date()
            if reply_date not in (TODAY, YESTERDAY):
                continue
            if NOW.hour > 0 and reply_date != TODAY:
                continue

            # validated; we can assume that the message is a reply to one that we have sent, and that we
            # sent our message today, unless it is currently less than an hour after midnight.
            hour_text = m.reply_to_message.text
            if hour_text not in HOURS:
                try:
                    m.reply("Sorry, you didn't reply to one of my time messages. Try again later!")
                except pawt.APIException:
                    # likely blocked
                    pass
                continue
            hour_ind = HOURS.index(hour_text)

            user_info[m.chat.id][hour_ind] = m.text


def hourly_action():
    hour_str = HOURS[NOW.hour - 1]
    for subscribed_chat_id in subscribed:
        chat = tg.chat(subscribed_chat_id)
        try:
            chat.send_message('What did you do during the following hour? '
                              'Reply to the following message so I can record it:', disable_notification=True)
            message = chat.send_message(hour_str, disable_notification=True, reply_markup=pawt.force_reply())

            preentered = user_info[subscribed_chat_id][NOW.hour - 1]  # entered with /next
            if preentered:
                message.reply(preentered)
        except pawt.APIException:
            # likely blocked
            pass


def send_recap():
    for chat_id, hourly_actions in user_info.items():
        if set(hourly_actions) == {None}:
            # no reported actions
            continue
        text = build_recap(hourly_actions)
        try:
            tg.chat(chat_id).send_message(text, parse_mode='Markdown', disable_notification=True)
        except pawt.APIException:
            # likely blocked
            pass
    for chat_id in user_info.keys():
        user_info[chat_id] = [None] * 24


def build_recap(hours):
    text = ','.join(hour or '' for hour in hours)
    day_name = '{} {}'.format(MONTHS[YESTERDAY.month], YESTERDAY.day)  # not the best way, I know
    return "Here's what you did on {}:\n\n```{text}```".format(day_name, text=text)


def finish():
    with open(os.path.join(FOLDER_PATH, 'data', 'user_info.json'), 'w') as f:
        json.dump(user_info, f)
    with open(os.path.join(FOLDER_PATH, 'data', 'subscribed.json'), 'w') as f:
        json.dump(list(subscribed), f)


if __name__ == '__main__':
    assert len(argv) == 2
    process_updates()
    if argv[1] == 'hourly':
        hourly_action()
    if argv[1] == 'daily':
        send_recap()
    finish()
