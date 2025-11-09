from vosk import Model ,  KaldiRecognizer#оффлайн распознание от vosk
from googlesearch import search #поиск в google
from pyowm import OWM #получение данных о погоде
from termcolor import colored #вывод цветных логов для выделения распознания речи
from dotenv import load_dotenv#загрузка информации из env файла
import speech_recognition #распознание пользовательской речи
import googletrans #использование системы Google Translate
import pyttsx3 #синтез речи
import wikipediaapi #поиск определений в wikipedia
import random #генератор случайных чисел
import webbrowser #для работы с браузером
import traceback #вывод traceback без остановки работы программы при отлове исключений
import json #работа с json файлами
import wave # создание и чтение аудиофайлов  формата wav
import os #работа с файловой системой

#информация о хозяйне асистента 
class OwnerPerson:
    """Информация о владельце """
    name=""
    home_city=""
    native_language="" 
    target_language=""

class VoiceAssistant:
    """настройка о голосовом асистенте"""
    name=""
    sex=""
    speech_language=""#язык речи клиента
    recognition_language=""#язык речи голосового помошника
class Translation:
    """получение вшитого в приложение перевода строк для создания мультиязычного асистента"""
    
    def __init__(self):
        """
        Конструктор класса - вызывается при создании объекта Translation
        В этот момент assistant уже создан, поэтому ошибки не будет
        """
        # Открываем файл с переводами в режиме чтения с кодировкой UTF-8
        with open("translation.json","r", encoding="UTF-8") as file:
            # Загружаем JSON из файла и превращаем в Python-словарь
            self.translations=json.load(file)
            # self.translations теперь содержит все переводы из файла
            # Например: {"hello": {"ru": "привет", "en": "hello"}}
    
    def get(self, text: str):
        """
        Метод для получения перевода текста на текущий язык ассистента
        
        :param text: исходный текст который нужно перевести
        :return: переведенный текст или исходный если перевод не найден
        """
        # Проверяем есть ли такой текст в нашем словаре переводов
        if text in self.translations:
            # Если есть - возвращаем перевод на текущем языке ассистента
            # assistant.speech_language - текущий язык (например "ru" или "en")
            # self.translations[text] - все переводы для этого текста
            # [assistant.speech_language] - конкретный перевод на нужном языке
            return self.translations[text][assistant.speech_language]
        else:
            # Если перевода нет - выводим сообщение в консоль красным цветом
            print(colored("Not translated phrase: {}".format(text),"red"))
            # И возвращаем исходный текст без изменений
            return text

#установка голоса  и  выбор языка 
def setup_assistant_voice():
    """установка  голоса по умолчанию"""
    voices =ttsEngine.getProperty("voices")#все доступные голоса из системы

    if assistant.speech_language=="en":#если англиский
        assistant.recognition_language="en-US"
        if assistant.sex=="female":#если женский пол
            ttsEngine.setProperty("voice",voices[1].id)#голос женский
        else:
            ttsEngine.setProperty("voice",voices[2].id)#голос мужскй
    else:#если русский
        assistant.recognition_language="ru-RU"
        ttsEngine.setProperty("voice",voices[0].id)

#функция для записывания голоса и перевода его в текст
def record_and_recognize_audio(*args: tuple):
    """Запись и распознанвание аудио"""
    with microphone:
        recognized_data=""#строка куда будет записываться то что говорит пользователь
        #запоминание шумов окружения для последующей очистки звука от них
        recognizer.adjust_for_ambient_noise(microphone,duration=2)#"Прислушивается к фоновым шумам" 2 секунды , запоминает шум кодиционера или ветра что бы потом его убрать
        
        try:
            print("Listening...")
            #Запись голоса
            audio=recognizer.listen(microphone,5,5)#слушем 5 секунд или пока ты не закончишь говорить , сохраняем записанный файл
            
            with open("microphone-results.wav","wb") as file:
                file.write(audio.get_wav_data())
        #если не услышал
        except speech_recognition.WaitTimeoutError:
            #помошник говорит я тебя не слышу
            play_voice_assistant_speech(translator.get("Can you check if your microphone is on,please?"))
            traceback.print_exc()#печатаем полную информацию об ошибке
            return
        #использование online распознования через Google
        try:
            print("Started recognition...")
            recognized_data=recognizer.recognize_google(audio,language=assistant.recognition_language).lower()#отправляем запись в google и переводим текст в нижний регистр
        except speech_recognition.UnknownValueError:#если помощник не понял то что ты сказал то он просто продолжает слушать
            pass
        #В случае проблем с доступом в Интернет происходит попытка использовать offline-распознование через Vosk
        except speech_recognition.RequestError:#если Google не работает то пытаемся разобрать самостоятельно
            print(colored("Trying to use offline recognition...","cyan"))
            recognized_data=use_offline_recognition()#пытаемся разобрать сами без интернета

        return recognized_data#возращаем результат распознаный текст или пустую строку или None
#функция для разбора речи если нет интернета(запасная проверка)
def use_offline_recognition():
    """переключение на оффлайн распознование"""
    recognized_data= ""#строка куда будет записываться то что говорит пользователь
    try:
        #проверка наличия модели на нужном языке в моделе если его нет то  говорим скачать и закрыть программу
        if not os.path.exists("models/vosk-model-small-"+assistant.speech_language +"-0.4"):#"models/vosk-model-small-"-папка с моделями + assistant.speech_language-добавляем язык для ассистента  +"-0.4 "- версия модели 
            print(colored("Please download the model from:\n"
                          "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.",
                          "red"))
            exit(1)
        #анализ записаного в микрофон аудио(что бы избежать повторов фразы)
        wave_audio_file=wave.open("microphone-results.wav","rb")#открываем запись голоса 
        model=Model("models/vosk-model-small-"+assistant.speech_language+"-0.4")#загружаем модель распознования модель-это как мозг который понимает речь
        offline_recognizer=KaldiRecognizer(model,wave_audio_file.getframerate())#настраивает механизм понимания голоса  KaldiRecognizer(model, ...)-Kaldi - движок для распознования речи , Recognizer-распознователь ,model-языковая модель(тот самый мозг с сервером), wave_audio_file.getframerate()-получаем чистоту записи  , нужно что бы узнать как читать файл

        #Выгружает ВСЮ запись из файла в память"
        data=wave_audio_file.readframes(wave_audio_file.getnframes())#wave_audio_file.readframes-читаем указанное количество кадров из файла ,wave_audio_file.getnframes()-сколько кадров в файле

        #проверяем запись->пытаемся понять речь->достаем текст
        if len(data)>0:#проверяем есть ли запись вообще
            if offline_recognizer.AcceptWaveform(data):#пытаемя разобрать что написанно  AcceptWaveform() - "принимаю звуковые волны для анализа"
                recognized_data=offline_recognizer.Result()#достаем результат распознования  , получаем что-то вроде: {"text": "привет как дела", "confidence": 0.85}
                #получение данных распознаного текста из JSON-строки(что бы можно было выдать другой ответ)
                recognized_data=json.loads(recognized_data)#разбираем json ответ , превращаем в python словарь
                recognized_data=recognized_data["text"]#достаем только чистый текст
    except:
        traceback.print_exc()#печатаем полную информацию об ошибке
        print(colored("Sorry,"))
#функция для того чтобы асистент мог говорить
def play_voice_assistant_speech(text_to_speech):
    """Проигрывание речи ответов голосового ассистента(без сохранения аудио)
       :params text_to_speech: текст, который нужно преоброзовать в речь"""
    ttsEngine.say(str(text_to_speech))#текст который должен сказать асистент
    ttsEngine.runAndWait()#сначало ждем пока асистент закончит говорить а потом только можно говорить что то ему

def play_greetings(*args: tuple):
    """
    Проигрывание случайной приветственной речи
    """
    greetings = [
        translator.get("Hello, {}! How can I help you today?").format(person.name),
        translator.get("Good day to you {}! How can I help you today?").format(person.name)
    ]
    play_voice_assistant_speech(greetings[random.randint(0, len(greetings) - 1)])


def play_farewell_and_quit(*args: tuple):
    """
    Проигрывание прощательной речи и выход
    """
    farewells = [
        translator.get("Goodbye, {}! Have a nice day!").format(person.name),
        translator.get("See you soon, {}!").format(person.name)
    ]
    play_voice_assistant_speech(farewells[random.randint(0, len(farewells) - 1)])
    ttsEngine.stop()
    quit()

#функция которая чтото ищет в google и открывает результат
def search_for_term_on_google(*args: tuple):#*args-принимаем любое количество аргументов и упаковываем их в 1 tuple-кортеж
    """Поиск в Google c автоматическим открытием 
    :param args: фраза поискового запроса"""
    if not args[0]: return #проверяем есть ли поисковой запрос
    search_term=" ".join(args[0])#собирает фразу для поиска объединят слова в 1 строку
    # 1 - ПРОСТОЙ ПОИСК С ОТКРЫТИЕМ СТРАНИЦУ ПОИСКА GOOGLE С МОИМ ЗАПРОСОМ
    #открытие ссылки  на поисковик в браузере
    url="https://google.com/search?q="+ search_term#Создает ссылку: https://google.com/search?q=как+готовить+суп
    webbrowser.get().open(url)#открываем в браузере и находим по url
    
    # 2-СЛОЖНЫЙ ПОИСК С САМОСТОЯТЕЛЬНЫМ ОТКРЫТИЕМ САЙТА 

    #автоматическое открытие результат(не безопасно)
    search_result=[]#список ссылок
    try:
        for _ in search(search_term,  # что искать
                        tld="com",  # верхнеуровневый домен
                        lang=assistant.speech_language,  # используется язык, на котором говорит ассистент
                        num=1,  # количество результатов на странице
                        start=0,  # индекс первого извлекаемого результата
                        stop=1,  # индекс последнего извлекаемого результата (я хочу, чтобы открывался первый результат)
                        pause=1.0,  # задержка между HTTP-запросами
                        ):
            search_result.append(_)#сохраняем ссылку в списке 
            webbrowser.get().open(_)#открываем ссылку в браузере
    #поскольку все ошибки предсказать будет сложно то будет призведен отлов
    except:#есои произошла ошибка 
        play_voice_assistant_speech(translator.get("Seems like we have a trouble.See logs for more information"))
        traceback.print_exc()#печатаем полную инфу о ошибке
        return
    print(search_result)#печатаем найденные ссылки 
    #ассистент озвучивает результат 
    play_voice_assistant_speech(translator.get("Here is what I found for {} on google").format(search_term))
#ищем видео на youtube и открываем результат поиска
def search_for_video_on_youtube(*args: tuple):#*args-принимаем любое количество аргументов и упаковываем их в 1 tuple-кортеж
    """Поиск видео на Youtube с автоматическим поиском открытием ссыдки на список результата
       :params args: фраза поискового запроса"""
    if not args[0]: return#проверяем есть ли поисковой запрос
    search_term=" ".join(args[0])#соедияем слова в предложения 
    url="https://www.youtube.com/results?search_query="+ search_term#ссоздаем ссылку для поиска с наши запросом-search_term
    webbrowser.get().open(url)#открываем браузер
    play_voice_assistant_speech(translator.get("Here is what I found for {} on youtube").format(search_term))#ассистент озвучивает
#ищем определенние в wikipedia и зачитываем результат
def search_for_definition_on_wikipedia(*args: tuple):
    """Поиск в wikipedia опреления с последеющим озвучиванием результатов и открытие ссылок
       :param args: фраза поискового запроса"""
    if not args[0]:return #проверяем есть ли поисковой запрос
    search_term=" ".join(args[0])#соедияем слова в предложения 

    #настраиваем википедию на нужный язык на язык на котором  говорит асистент
    wiki=wikipediaapi.Wikipedia(assistant.speech_language)

    #поиск страницы по запросу , чтение summary , открытие ссылки на страницу для  получение подробной информации
    wiki_page=wiki.page(search_term)#ищем страницу в википедии
    try:
        if wiki_page.exists():#если страница  найденна
            play_voice_assistant_speech(translator.get("Here is what I found for {} on Wikipedia").format(search_term))#озвучиваем
            webbrowser.get().open(wiki_page.fullurl)#открываем страницу в википедии

            #чтение ассистентом первых 2 предложений summary с страницы Wikipedia
            play_voice_assistant_speech(wiki_page.summary.split(".")[:2])
        else:#если страница не найдена
            #открытие  ссылки на поисковик в браузере
            play_voice_assistant_speech(translator.get(
                "Can't find {} on Wikipedia. But here is what I found on google").format(search_term))
            url = "https://google.com/search?q=" + search_term
            webbrowser.get().open(url)#открываем поиск в google

    except:#если произошла ошибка 
        play_voice_assistant_speech(translator.get("Seems like we have a trouble. See logs for more information"))
        traceback.print_exc()
        return
#функция чтобы язык пользователя и язык ассистента совподали
def get_translation(*args: tuple):
    """Получение перевода текста с 1 языка на другой"""
    if not args[0]: return#если аргументов нет

    search_term=" ".join(args[0])#соедияем слова в предложения 
    google_translator=googletrans.Translator()#создаем переводчик
    Translation_result=""#

    old_assistant_language=assistant.speech_language#запоминаем текущий язык
    try:
        #если язык речи ассистента и родной язык пользователя различаются , то перевод выполняется на родной язык
        if assistant.speech_language != person.native_language:
            translation_result=google_translator.translate(search_term,#что перевести
                                                           src=person.target_language,#с какого языка  
                                                           dest=person.native_language)#на какой язык
            play_voice_assistant_speech("The translation for {} in Russia is".format(search_term))

            #смена голоса асистента на родной язык пользователя (что бы можно было произнести перевод)
            assistant.speech_language=person.native_language
            setup_assistant_voice()
        else:#если язык пользователя и ассистента совпадают
            translation_result=google_translator.translate(search_term,#что перевести 
                                                           src=person.native_language,#с какого языка 
                                                           dest=person.target_language)#на какой
            play_voice_assistant_speech("По-англиски {} будет как".format(search_term))
            #смена голоса асистента на изучаемый язык пользователем
            assistant.speech_language=person.target_language
            setup_assistant_voice()#переключаем голос на язык перевода
        #произнесенние перевода
        play_voice_assistant_speech(translation_result.text)
    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble.See logs for more information"))
        traceback.print_exc()
    finally:
        #возращение преждних настроек голоса
        assistant.speech_language=old_assistant_language
        setup_assistant_voice()
#получение погоды  и рассказываем о погоде
def get_weather_forecast(*args: tuple):
    """Получение и озвучивание прогноза погоды
       :params args: город,по которому должеенвыполнятся запрос"""
    #в случае наличия дополнительного аргумента-запрос погоды происходит по нему
    #иначе-используется город заданый в настройках
    if args[0]:#если аргументы есть
        city_name=args[0][0]#берем город мз аргументов
    else:
        city_name=person.home_city#берем город из настроек
    try:
        #Получения данных о погоде
       
        weather_api_key=os.getenv("WEATHER_API_KEY")#ключ API
        open_weather_map=OWM(weather_api_key)#подключаемся к сервичу погоды

        #запрос данных о текущем состоянии погоды
        weather_manager=open_weather_map.weather_manager()#открываем сервер погоды
        observation=weather_manager.weather_at_place(city_name)#запрашиваем погоду
        weather=observation.weather#получаем данные

    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble.See logs for more information"))
        traceback.print_exc()
        return
    
    #извлекаем данные о погоде
    status=weather.detailed_status#пасмурно или ясно 
    temperature=weather.temperature('celsius')["temp"]#температура в градуссах 
    wind_speed=weather.wind()["speed"]#скорость ветра
    pressure=int(weather.pressure["press"] / 1.333) #давление

    print(colored("Weather in " + city_name +
                  ":\n * Status: " + status +
                  "\n * Wind speed (m/sec): " + str(wind_speed) +
                  "\n * Temperature (Celsius): " + str(temperature) +
                  "\n * Pressure (mm Hg): " + str(pressure), "yellow"))
     # озвучивание текущего состояния погоды ассистентом
    play_voice_assistant_speech(translator.get("It is {0} in {1}").format(status, city_name))
    play_voice_assistant_speech(translator.get("The temperature is {} degrees Celsius").format(str(temperature)))
    play_voice_assistant_speech(translator.get("The wind speed is {} meters per second").format(str(wind_speed)))
    play_voice_assistant_speech(translator.get("The pressure is {} mm Hg").format(str(pressure)))
#функция переключения между англиским и русским можно потом будет сделать кнопку
def change_language(*args: tuple):
    """Изменение языка голосового ассистента(языка распознования речи)"""
   #Если сейчас "en" (английский) → ставит "ru" (русский)
   #Если сейчас "ru" (русский) → ставит "en" (английский)
    assistant.speech_language="ru" if assistant.speech_language=="en" else "en"
    setup_assistant_voice()#обновляем голос ассистента
    print(colored("Language switched to "+assistant.speech_language,"cyan"))
#ищем человека в сотсетях в вконтакте и в facebook
def run_person_through_social_nets_databases(*args: tuple):
    """Поиск человека по базе данных специальных сетей Вконьакте и Facebook
       :param args: имя , фамилия TODO город
    """
    if not args[0]: return #если нет аргументов

    google_search_term=" ".join(args[0])
    vk_search_term="_".join(args[0])
    fb_search_term="-".join(args[0])
    #ищем vk через google
    url="https://google.com/search?q=" + google_search_term+"site: vk.com"
    webbrowser.get().open(url)
    #ищем facebook через google
    url="https://google.com/search?q=" + google_search_term+"site: facebook.com"
    webbrowser.get().open(url)

    #ищем на прямую в сотсетях vk
    vk_url="https://vk.com/people/"+vk_search_term# "https://vk.com/people/Иван_Петров"
    webbrowser.get().open(vk_url)
    #ищем на прямую в сотсетях facebook
    fb_url="https://www.facebook.com/public/"+fb_search_term # "https://facebook.com/public/Иван-Петров"
    webbrowser.get().open(fb_url)

    play_voice_assistant_speech(translator.get("Here is what I found for {} on social nets").format(google_search_term))
#функция которая подбрасывает монетку 3 раза и объявляет победителя
def toss_coin(*args: tuple):
    """Подбрасывание монетки для выбора 2 опций"""
    flips_count,heads,tails=3,0,0 #количество подбрасываний , счетчик орлов, счетчик решек
    #подбрасывание монетки 
    for flip in range(flips_count):
        if random.randint(0,1)==0:# случайное число 0 или 1
            heads +=1  # если 0 - увеличиваем "орлы"
        
    tails=flips_count - heads  # "решки" = всего бросков - "орлы"
    #определение победителя 
    winner="Tails" if tails > heads else "Heads"
    play_voice_assistant_speech(translator.get(winner)+ " "+translator.get("won"))

#функция которая находит  команду по ее названию  
def execute_command_with_name(command_name: str, *args: list):#получаем command_name- имя команды-Погода  args-аргумент команды-Москва
    """Выполнение заданной пользователем команды и аргументами
    :param command_name: название команды
    :param args: аргументы, которые будут переданы в метод
    :return:"""

    for key in commands.keys():#перебираем все ключи кортижи
        if command_name in key:#если команда есть в кортеже
            commands[key](*args)#выполняем функцию с ее аргументами например Погода Москва -погода имя функции москва - аргумент
        else:
            pass #print ("command not found")
        
# перечень команд для использования (качестве ключей словаря используется hashable-тип tuple)
# в качестве альтернативы можно использовать JSON-объект с намерениями и сценариями
# (подобно тем, что применяют для чат-ботов)
commands = {
    ("hello", "hi", "morning", "привет"): play_greetings,
    ("bye", "goodbye", "quit", "exit", "stop", "пока"): play_farewell_and_quit,
    ("search", "google", "find", "найди"): search_for_term_on_google,
    ("video", "youtube", "watch", "видео"): search_for_video_on_youtube,
    ("wikipedia", "definition", "about", "определение", "википедия"): search_for_definition_on_wikipedia,
    ("translate", "interpretation", "translation", "перевод", "перевести", "переведи"): get_translation,
    ("language", "язык"): change_language,
    ("weather", "forecast", "погода", "прогноз"): get_weather_forecast,
    ("facebook", "person", "run", "пробей", "контакт"): run_person_through_social_nets_databases,
    ("toss", "coin", "монета", "подбрось"): toss_coin,
}
if __name__ == "__main__":
    # ПРОВЕРКА МИКРОФОНОВ
    print("=== ПРОВЕРКА МИКРОФОНОВ ===")
    microphones = speech_recognition.Microphone.list_microphone_names()
    for i, name in enumerate(microphones):
        print(f"{i}: {name}")
    
    # Пробуем микрофон №1
    microphone = speech_recognition.Microphone(device_index=1)

    # Остальная инициализация
    recognizer = speech_recognition.Recognizer()
    ttsEngine = pyttsx3.init()
    
    person = OwnerPerson()
    person.name = "Мирон"
    person.home_city = "Екатеринбург" 
    person.native_language = "ru"
    person.target_language = "en"

    assistant = VoiceAssistant()
    assistant.name = "Алиса"
    assistant.sex = "female"
    assistant.speech_language = "ru"
    assistant.recognition_language = "ru-RU"
    
    setup_assistant_voice()
    translator = Translation()
    load_dotenv()
    

    # ГОЛОСОВОЙ ВВОД
    while True:
        voice_input = record_and_recognize_audio()
    
        if not voice_input or len(voice_input.strip()) == 0:
            continue
    
        print(colored(voice_input, "blue"))
        parts = voice_input.split(" ")
        command = parts[0]
        command_options = parts[1:] if len(parts) > 1 else []
        execute_command_with_name(command, command_options)

# ДОБАВЬ ЭТО ПОСЛЕ блока if __name__ == "__main__": (на одном уровне с ним)
def init_assistant():
    """Инициализация ассистента для использования в веб-версии"""
    global person, assistant, translator, ttsEngine, recognizer, microphone
    
    # Инициализация объектов
    person = OwnerPerson()
    assistant = VoiceAssistant()
    
    # Инициализация TTS
    ttsEngine = pyttsx3.init()
    
    # Инициализация распознавания речи
    try:
        microphone = speech_recognition.Microphone(device_index=1)
    except:
        microphone = speech_recognition.Microphone()
    recognizer = speech_recognition.Recognizer()
    
    # Инициализация переводчика
    translator = Translation()
    
    # Настройка голоса
    setup_assistant_voice()
    
    load_dotenv()
    
    print("Ассистент инициализирован для веб-версии")

# Автоматическая инициализация при импорте
init_assistant()