import telebot
import speech_recognition as sr
import requests
from gtts import gTTS
import os
from pydub import AudioSegment
import random
import string


'''
Esses são configurações necessárias para o bot funcionar.
Você deve fonecer seu próprio token do telegram e api_key do chatgpt.

Aqui você pode configurar os parâmentros da api, 'max tokens' e 'temperature',
caso tenha dúvidas olhe a documentação da api, lá vai encontar também outros parâmetros
que podem ser usados.

Como este bot utiliza a api do chatgpt, que é paga, eu restringi ele a responde somente
a um usuário para que outras pessoas não usem, basta preencher o seu id do Telegram
e o bot responderá somente pra você.

Você pode remover essa opção alterando o '@bot.message_handler' da função 'message_handler',
mas tenha em mente que assim qualquer um poderá utilizar seu bot, consequentemente seu créditos na api.
'''

telegram_token = '<SEU-TOKEN-DO-TELEGRAM>'
chatgpt_api_key = '<SUA-API-KEY>'
user_id = 000000000 #<SEU-ID-DE-USUARIO> DEVE SER NUMÉRICO

chatgpt_max_tokens = 500
chatgpt_temperature = 0.7

pasta_de_audio = os.path.join(os.getcwd(), 'audios')

language = 'pt-BR'

# initialize the Telegram bot with the API token
bot = telebot.TeleBot(telegram_token)

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    text = ("https://github.com/EdCarlosBicudo/voice_gpt"
            "\nDesenvolvido por: Ed Carlos Bicudo.")

    bot.reply_to(message, text)


def converter_audio(file_name):
    if not os.path.exists(pasta_de_audio):
        os.makedirs(pasta_de_audio)

    path_wav = f"{file_name}.wav"

    sound = AudioSegment.from_file(file_name, "ogg")
    
    sound.export(path_wav, format="wav")

    return path_wav


def get_audio_file(file_id):
    file_info = bot.get_file(file_id)
    
    file_name = file_info.file_path.split('/')[1]
    
    path = os.path.join(pasta_de_audio, file_name)
    
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open(path, 'wb') as new_file:
        new_file.write(downloaded_file)

    return path

def call_gpt_api(prompt):

    prompt_completo = f"Gere uma resposta para o prompt a seguir de maneira não estruturada, otimizada para converter para áudio, prompt: {prompt}"

    response = requests.post('https://api.openai.com/v1/completions', 
                             headers={'Content-Type': 'application/json',
                                      'Authorization': chatgpt_api_key},
                             json={
                                 "model": "text-davinci-003",
                                 'prompt': prompt_completo,
                                 'max_tokens': chatgpt_max_tokens,
                                 'temperature': chatgpt_temperature
                             })
    
    return response.json()['choices'][0]['text']


def esvaziar_pasta():
    for filename in os.listdir(pasta_de_audio):
        file_path = os.path.join(pasta_de_audio, filename)

        try:
            os.remove(file_path)
        except Exception as e:
            print(e)


# create a function to handle incoming audio messages
@bot.message_handler(content_types=['voice'], func=lambda message: message.from_user.id == user_id)
def handle_audio(message):

    path = get_audio_file(message.voice.file_id)

    audio = converter_audio(path)

    r = sr.Recognizer()
    with sr.AudioFile(audio) as source:
        audio_text = r.recognize_google(r.record(source), language=language)

    bot.send_message(message.chat.id, f"PROMPT: {audio_text}")

    # send the text to the ChatGPT API and get the response
    response_text = call_gpt_api(audio_text)

    # convert the response text to speech using gTTS library
    # Using ramdom file names to avoid conflict
    file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    response_path = os.path.join(pasta_de_audio, f"{file_name}.mp3")
    tts = gTTS(text = response_text, lang = language)
    tts.save(response_path)

    # send the speech response back to the user
    with open(response_path, 'rb') as audio:
        bot.send_voice(message.chat.id, audio)

    esvaziar_pasta()

# start the bot
bot.infinity_polling()