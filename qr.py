import vk_api
import requests
from random import randint
from PIL import Image
#python3.7 не поддерживает Pillow, так что используем 3.6 или ниже
import pyqrcode
from time import sleep
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
from multiprocessing import Process, Queue
#так же через пип должен быть установлен модуль pypng

from datetime import datetime
from os import remove

class ToDo:
    def __init__(self):
        self.q = Queue()#очередь с путями к изображениям, которые буду выгружать в группу

    def do_qr(self, url): #создаем qr_code в формате png
        url = pyqrcode.create(url)
        way = 'photos/'+str(randint(1,999999))+'.png'
        url.png(way,
                scale=10, 
                module_color=[0,0,0,255], 
                background=[0xff, 0xff, 0xff]) #в way создаст код с инфой из url
        return way

    def do_photo(self,name): #qr_code клеим в шаблон (foto.png)
        img = Image.open('foto.png').convert("RGBA")
        mark = Image.open(name).convert("RGBA") 
        img.paste(mark, (90, 100), mark)
        new_name = 'qrs/'+str(randint(1,999999))+'.png'
        img.save(new_name)
        self.q.put(new_name)
        remove(name) 

    def messaging(self):
        vk_session = vk_api.VkApi('login', 'pass')
        vk_session.auth(token_only=True)
        upload = vk_api.VkUpload(vk_session)

        vk_session2 = vk_api.VkApi(token='token')
        vk2 = vk_session2.get_api()

        while True:
            name = self.q.get()

            #грузим в альбом
            photo = upload.photo(name, album_id='a_id', 
                                        group_id='g_id')

            attachments = []
            attachments.append(
                'photo{}_{}'.format(photo['owner_id'], photo['id'])
            )

            #отправляем в ЛС
            vk2.messages.send(
                user_id='u_id',
                attachment=','.join(attachments),
                message='Ваш код готов!',
                random_id=randint(1, 999999)
            )

            sleep(0.5)


to = ToDo()

def play():
    while True:
        name = to.do_qr('some_link')
        to.do_photo(name)
        sleep(0.1)

for i in range(3):
    proc = Process(target=play, args=())
    proc.start()    

proc = Process(target=to.messaging, args=())
proc.start() 


