import vk_api
import requests
from random import randint
from PIL import Image
#python3.7 не поддерживает Pillow(одни проблемы с ним), так что используем 3.6 или ниже
import pyqrcode
from time import sleep
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
from multiprocessing import Process, Queue
#так же через пип должен быть установлен модуль pypng, импортить его не нужно

from datetime import datetime
from os import remove

class ToDo:
    """
        С помощью пиллоу склеиваю шаблон и кьюаркод,
        потом отправляю его в альбом группы, от имени которой общается бот,
        который и отправляет это всё мне в лс.
        Чтобы проверить работоспособность достаточно написать что-то боту https://vk.com/public180755234,
        везде прописать свой логин и пароль от вк, а в фукнции sending добавить свой айди, вместо моего:
        vk.messages.send(
            user_id = **********...
        Максимальное быстродействие у меня было при таком количестве процессов, как тут.
        Но скорость все равно оставляет желать лучшего, надеюсь, из-за интернет-соединения
    """
    def __init__(self):
        self.q = Queue()#очередь с путями к изображениям, которые буду выгружать в группу
        self.q2 = Queue()#ссылка на фотографии в вк, которые кидаю в лс
        
    def do_qr(self, url): #создаем qr_code в формате png
        url = pyqrcode.create(url)
        way = 'photos/'+str(randint(1,999999))+'.png'#такая сложность нужна, 
                                                    #чтобы вдруг не создать две одинаковых картинки
        url.png(way,
                scale=10, 
                module_color=[0,0,0,255], 
                background=[0xff, 0xff, 0xff]) #в way создаст код с инфой из url
        return way

    def do_photo(self,name): #qr_code клеим в шаблон (foto.png)
        img = Image.open('foto.png').convert("RGBA")
        mark = Image.open(name).convert("RGBA") #без конвертации кидается ошибками
        img.paste(mark, (90, 100), mark)
        new_name = 'qrs/'+str(randint(1,999999))+'.png'
        img.save(new_name)
        self.q.put(new_name)
        remove(name) #удаляем картинощку

    def photo_load(self, upload): #грузим шаблон с кодом в альбом группы(эта операция не чаще чем раз в 0.5 сек)
        while True:
            name = self.q.get()
            photo = upload.photo( name,
                                    album_id=a_id,
                                    group_id=g_id
            )
            photos = '{}_{}'.format(
                photo[0]['owner_id'], photo[0]['id']
            )
            remove(name) #удаляем изображение

            self.q2.put(photos)
            sleep(0.5)
            
    def album(self):
        login, password = 'login', 'pass'#вк кидает ошибку, если аутентифицироваться
                                                            #не в функции. причину не нашел
        vk_session = vk_api.VkApi(login, password)
        try:
            vk_session.auth(token_only=True)
        except vk_api.AuthError as error_msg:
            print(error_msg)
        vk = vk_session.get_api()
        while True:
            url = []
            for _ in range(self.q2.qsize()):
                photos = self.q2.get()         
                url.append(vk.photos.getById(photos=photos, extends=0)[0]['sizes'][6]['url'])

                self.sending(url)
        
    def sending(self,urls):
        vk_session = vk_api.VkApi( #токен группы
            token=access_token)

        longpoll = VkLongPoll(vk_session)
        vk = vk_session.get_api()
        attachments = []
        upload = VkUpload(vk_session)
        session = requests.Session()

        for url in urls:
            image = session.get(url, stream=True)
            photo = upload.photo_messages(photos=image.raw)[0]
            attachments.append(
                'photo{}_{}'.format(photo['owner_id'], photo['id'])
            )
            
            vk.messages.send(
                user_id=u_id, #кому отправляем
                attachment=','.join(attachments),
                message='Ваш код готов!',
                random_id = randint(1, 999999)
                )


to = ToDo()

def play():
    while True:
        name = to.do_qr('some_link')
        to.do_photo(name)
        sleep(0.1)

for i in range(3):
    proc = Process(target=play, args=())
    proc.start()    


login, password = 'login', 'pass'
vk_session = vk_api.VkApi(login, password)
try:
    vk_session.auth(token_only=True)
except vk_api.AuthError as error_msg:
    print(error_msg)
upload = vk_api.VkUpload(vk_session)
vk = vk_session.get_api()

proc = Process(target=to.photo_load, args=(upload,))
proc.start()

for i in range(5):
    proc = Process(target=to.album, args=())
    proc.start() 


