import steam.webauth as wa
import json
import base64
from bs4 import BeautifulSoup
import imaplib
import email
import datetime
import time
import keyboard
import random
import glob
import pyautogui
import threading
import winsound

util = 'util/'
with open(util + 'info.json', 'r') as f:
    info = json.loads(f.read())
    steam_email = info['steam_email']
    email_pass = base64.b64decode(info['email_pass']).decode()
    steam_user = info['steam_user']
    steam_pass = base64.b64decode(info['steam_pass']).decode()
    steam_link = info['steam_link']
imap_server = "imap.gmail.com"
upload_url = "https://steamcommunity.com/actions/FileUploader"
stop_key = "="
trigger_key = "]"
stop = False
switch = False

def get_code():
    code = None
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(steam_email, email_pass)
    while not code:
        mail.select('inbox')

        result, data = mail.search(None, '(UNSEEN FROM "noreply@steampowered.com" SUBJECT "Your Steam account: Access from new web or mobile device")')
        mail_ids = data[0]

        id_list = mail_ids.split()

        if len(id_list) > 0:
            result, data = mail.fetch(str(int(id_list[-1])), '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if datetime.datetime.now() - datetime.datetime.strptime(" ".join(msg['Date'].split(" ")[:5]), "%a, %d %b %Y %H:%M:%S") < datetime.timedelta(hours=2):
                        code = msg.get_payload()[0].get_payload(decode=True).decode().split('\n')[5].strip()
                        if code:
                            print("Email code found, code = " + str(code))
                            mail.close()
                            return code
                        else:
                            print("Email code not found yet")
        else:
            print("Email code not found yet")
        time.sleep(5)

def get_data(r, file):
    soup = BeautifulSoup(r.content, 'html.parser')
    form = soup.find('form', id='avatar_upload_form')
    data = dict()
    for e in form.find_all('input'):
        data[e['name']] = (None, e['value'])
    data['avatar'] = ('blob', open(file, 'rb').read())
    return data

def trigger():
    if pyautogui.locateOnScreen(util + 'trigger.png', confidence=0.5, region=(1920-500, 0, 500, 500)):
        return True
    else:
        return False

def watcher():
    global stop, switch
    while not stop:
        time.sleep(0.3)
        if keyboard.is_pressed(stop_key):
            print('Exiting...')
            stop = True
        if keyboard.is_pressed(trigger_key):
            switch = True

def main():
    global file, stop, switch
    print('Logging into steam...')
    user = wa.WebAuth(steam_user, password=steam_pass)
    success = False
    while not success:
        try:
            user.login()
        except wa.HTTPError:
            print('Connection failed, retrying...')
            time.sleep(5)
        except wa.EmailCodeRequired:
            print('Connected to server')
            success = True
    success = False
    while not success:
        time.sleep(5)
        code = input("code: ")#get_code()
        try:
            sess = user.login(steam_pass, email_code=code)
            success = True
        except:
            pass
    form = sess.post(steam_link)
    watch = threading.Thread(target=watcher, args=())
    watch.start()
    print(f'Logged into steam, watching for kills (hold "{stop_key}" to stop)')
    print(f'Hold {trigger_key} to switch PFP at any time')
    while not stop:
        if trigger() or switch:
            winsound.PlaySound(util + 'alert.wav', winsound.SND_FILENAME)
            print('Changing PFP...')
            file = random.choice(glob.glob('images/*'))
            data = get_data(form, file)
            r = sess.post(upload_url, files=data)
            switch = False
            print('PFP changed to ' + str(file))
            time.sleep(3)
        time.sleep(1)

if __name__ == '__main__':
    main()
