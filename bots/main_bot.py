from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re

@respond_to('play (.*)')
def play(message, music):
    message.reply('play %s?' % music)

@respond_to('list')
def love(message):
    message.reply('music list:')

@listen_to('Can someone help me?')
def help(message):
    # Message is replied to the sender (prefixed with @user)
    message.reply('Yes, I can!')

    # Message is sent on the channel
    message.send('I can help everybody!')

    # Start a thread on the original message
    message.reply("Here's a threaded reply", in_thread=True)
