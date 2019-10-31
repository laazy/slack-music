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
        elif n['type'] == 'playlist':
            if n['len'] > n['index']:
                musicUrl = requests.get(musicApi + '/song/url?id=%s' % (n['src']['playlist']['tracks'][n['index']]['id']))
                res = json.loads(musicUrl.text)
                n['song'] = n['src']['playlist']['tracks'][n['index']]['name']
                n['index'] = n['index'] + 1
                _thread.start_new_thread(playone, (res['data'][0]['url'],))
            else:
                music_queue.put({'action': 'nextp'})

    except Exception as e:
        # skip this one
        music_queue.put({'action': 'next'})
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
        if msg['action'] == 'add':
            music_list.append(msg['music'])
        elif msg['action'] == 'next':
            os.system('killall mplayer')
            if len(music_list) > 0 and music_list[0]['type'] == 'playlist':
                playnext(music_list[0])
            elif len(music_list) > 1:
                playnext(music_list[1])
                music_list.pop(0)
            elif len(music_list) > 0:
                playnext(music_list[0])
        elif msg['action'] == 'nextp':
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
        elif msg['action'] == 'top':
            music_list[0] == msg['music']
            music_list.remove(msg['music'])

_thread.start_new_thread(playing, ())

@respond_to('addid (.*)')
def addid(message, music):
    message.reply('success')
    music_queue.put({'action': 'add', 'music': {'type':'id', 'src': music, 'from': message.user['real_name']}})
    
@respond_to('add (.*)')
def add(message, keyword):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "keyword", "src": keyword, 'from': message.user['real_name']}})

@respond_to('addp (.*)')
def addp(message, id):
    try:
        res = json.loads(requests.get(musicApi + '/playlist/detail?id=%s&s=0' % (id)).text)
        music_queue.put({"action": "add", "music": {"type": "playlist", "src": res, 'id': id, 'index': 0, 'song': res['playlist']['tracks'][0]['name'], 'len': len(res['playlist']['tracks']), 'from': message.user['real_name']}})
        message.reply('success')
    except:
        message.reply('something wrong')

@respond_to('addln (.*)', re.IGNORECASE)
def addln(message, name):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "localn", "src": name, 'from': message.user['real_name']}})

@respond_to('addli (.*)', re.IGNORECASE)
def addli(message, name):
    message.reply('success')
    music_queue.put({"action": "add", "music": {"type": "localid", "src": name, 'from': message.user['real_name']}})

@respond_to('start', re.IGNORECASE)
def start(message):
    message.reply('success')
    music_queue.put({"action": "start"})
    
@respond_to('stop', re.IGNORECASE)
def stop(message):
    message.reply('success')
    music_queue.put({"action": "stop"})

@respond_to('nextp$', re.IGNORECASE)
def nextp(message):
    message.reply('success')
    music_queue.put({"action": "nextp"})

@respond_to('next$', re.IGNORECASE)
def next(message):
    message.reply('success')
    music_queue.put({"action": "next"})



@respond_to('list (.*)', re.IGNORECASE)
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

@respond_to('listp (.*)', re.IGNORECASE)
def listP(message, keywords):
    try:
        res = json.loads(requests.get(musicApi + '/search?limit=12&type=1000&keywords=' + keywords).text)
        for playlist in res['result']['playlists']:
            message.reply('id: %s %s 歌单长度：%s' % (playlist['id'], playlist['name'], playlist['trackCount']))
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to('detailp ([0-9]*) ([0-9]*)', re.IGNORECASE)
def detailP(message, id, offset):
    try:
        res = json.loads(requests.get(musicApi + '/playlist/detail?s=0&id=%s' % (id)).text)
        i = 0
        ioff = int(offset) 
        message.reply('歌单总长度：%d' % (len(res['playlist']['tracks'])))                               
        for track in res['playlist']['tracks'][ioff:ioff+10]:
            message.reply('id: %s name: %s index: %d' % (track['id'], track['name'], ioff+i))
            i = i + 1
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to(r"top (\d+)")
def top(message, id):
    id = int(id)
    if id > len(music_list) or id < 2:
        message.reply("顶歌失败,id不正确")
    else:
        music_queue.put({"action": "top", "music": music_list[id + 1]})
        message.reply("顶歌成功")

@respond_to('local (.*)', re.IGNORECASE)
def locals(message, start=0):
    try:
        for i in os.listdir(localstorage)[int(start):int(start)+10]:
            message.reply(i)
    except Exception as e:
        print(e)
        message.reply('out of range')

@respond_to('localnum', re.IGNORECASE)
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
            if m['type'] == 'playlist':
                message.reply('%d: 歌名：%s 歌单id：%s 第%d首 from: %s' % (i, m['song'], m['id'], m['index'], m['from']))
            else:
                message.reply('%d: 歌名orID：%s from: %s' %(i, m['src'], m['from']))
            i += 1
    except Exception as e:
        print(e)
        message.reply('something wrong')

@respond_to('help')
def help(message):
    message.reply(
"""
list %s 关键字搜索单曲
listp %s 关键字搜索歌单
add %s 添加歌曲（使用关键字搜索出的第一条）
addp %s 添加指定id歌单
detailp %s %d 查看指定id歌单的详情，需要填入offset，只返回10条结果
addid %d 添加指定id歌曲
addln %s （本地）添加歌曲
addli %d （本地）添加指定id歌曲
show    查看排队列表
start   开始播放
next    下一首歌（如果在播放歌单，则为歌单中下一首）
nextp   跳过当前歌单（跳到下一个记录）
stop    停止播放
top %d  顶歌 """)
