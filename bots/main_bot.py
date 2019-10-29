from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re
import requests
import json
import os
import queue
import _thread

musicApi = os.getenv('MusicAPI')
localstorage = '/home/pi/Music'

music_queue = queue.Queue()

def playnext(n):
    try:
        if n['type'] == 'id':
            musicUrl = requests.get(musicApi + '/song/url?id=%s' % (n['src']))
            res = json.loads(musicUrl.text)
            _thread.start_new_thread(playone, (res['data'][0]['url'],))
        elif n['type'] == 'keyword':
            search_res = json.loads(requests.get(musicApi + '/search?limit=1&keywords=%s' % (n['src'])).text)
            url_res = json.loads(requests.get(musicApi + '/song/url?id=%d' % (search_res['result']['songs'][0]['id'])).text)
            _thread.start_new_thread(playone, (url_res['data'][0]['url'],))
        elif n['type'] == 'localn':
            _thread.start_new_thread(playone, (localstorage + '/' + n['src'],))
        elif n['type'] == 'localid':
            name = os.listdir(localstorage)[int(localid)]
            _thread.start_new_thread(playone, (localstorage + '/' + name,))
    except Exception as e:
        print(e)

def playone(url):
    cmd = 'mplayer %s < /dev/null > /dev/null 2>&1' % (url) # backend
    res = os.system(cmd)
    if (res == 0):
        music_queue.put({'action': 'next'})

music_list = []

def playing():
    while True:
        msg = music_queue.get()
        print(msg)
        if msg['action'] == 'add':
            music_list.append(msg['music'])
        elif msg['action'] == 'next':
            os.system('killall mplayer')
            if len(music_list) > 1:
                playnext(music_list[1])
                music_list.pop(0)
            elif len(music_list) > 0:
                playnext(music_list[0])
        elif msg['action'] == 'stop':
            os.system('killall mplayer')
        elif msg['action'] == 'start':
            if len(music_list) > 0:
                playnext(music_list[0])
        elif msg['action'] == 'show':
            msg['callback'](music_list)

_thread.start_new_thread(playing, ())

@respond_to('addid (.*)')
def playid(message, music):
    music_queue.put({'action': 'add', 'music': {'type':'id', 'src': music}})
    message.reply('success')

@respond_to('add (.*)')
def play(message, keyword):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "keyword", "src": keyword}})

@respond_to('addln (.*)')
def play(message, name):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "localn", "src": name}})

@respond_to('addli (.*)')
def play(message, name):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "localid", "src": name}})


@respond_to('start')
def stop(message):
    message.reply('success')
    music_queue.put({"action": "start"})
    

@respond_to('stop')
def stop(message):
    message.reply('success')
    music_queue.put({"action": "stop"})

@respond_to('next')
def stop(message):
    message.reply('success')
    music_queue.put({"action": "next"})

@respond_to('list (.*)')
def listM(message, keywords):
    try:
        res = json.loads(requests.get(musicApi + '/search?limit=8&keywords=' + keywords).text)
        for song in res['result']['songs']:
            artist = "佚名"
            try:
                artist = song['artists'][0]['name']
            except:
                print("no artist")
            message.reply('%s %s %s' % (song['id'], song['name'], artist))
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to('local (.*)')
def locals(message, start=0):
    try:
        for i in os.listdir(localstorage)[int(start):int(start)+10]:
            message.reply(i)
    except Exception as e:
        print(e)
        message.reply('out of range')

@respond_to('localnum')
def localnum(message):
    try:
        message.reply(str(len(os.listdir(localstorage))))
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to('show')
def show(message):
    try:
        i = 1
        for m in music_list:
            message.reply('%d: ' %(i) + json.dumps(m, ensure_ascii=False))
            i += 1
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to('help')
def help(message):
    message.reply("""list %s 关键字搜索
    add %s 播放歌曲（使用关键字搜索出的第一条）
    addid %d 指定id播放歌曲
    show    查看排队列表
    start   开始播放
    next    下一首歌
    stop    停止播放""")
