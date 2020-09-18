# Importações de libs basicas e de input e ouput
import io
import os
from math import ceil
import base64
from io import BytesIO

# Importações das APIs do Google
from google.cloud import vision, translate
from google.cloud.vision import types
from googleapiclient.discovery import build

# import keys
import keys
api_key = keys.api
cse_id = keys.cse

# Importações das lib de manipulação de imagens
import cv2
from PIL import Image
import numpy as np
from matplotlib import pyplot

# Importações das APIs de reconhecimento de cores
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc, service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
import os
from google.cloud import vision, translate

# from principal_functions import sample_translate_text

# Declaração da credencial para APIs do Google e instancia do client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="projeto-tcc-276919-afa464aedacb.json"
client = vision.ImageAnnotatorClient()

# Declaração e intancia de client da API da Clarifai
channel = ClarifaiChannel.get_json_channel()
stub = service_pb2_grpc.V2Stub(channel)

#Função que converte uma string em base64 para uma imagem em numpy array 
#---RETORNO: a imagem que antes estava em string (numpy array).
def base64_to_image(base64_image_string):
    # abre a imagem a partir de um buffer de bites que veio da conversão da base64
    image = Image.open(BytesIO(base64.b64decode(base64_image_string)))
    img = np.array(image) # converte a Image object em um vetor numpy
    
    return img

#Função que converte uma imagem passada em vetor numpy para o formato binario e em base64
#---RETORNO: um vetor com a imagem em binario [0] e em base64 [1].
def image_to_base64_and_bin(image):
    response = [] # inicializa o vetor que vai receber as imagens nas duas formas
    pil_img = Image.fromarray(image) # converte o numpy array pra um Image object
    buff = BytesIO() # inicializa um buffer binario
    pil_img.save(buff, format="JPEG")    
    #pil_img.save(buff, format="PNG")
    #pil_img.save(buff) # salva a imagem no buffer
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8") # codifica a imagem em base64  
    
    response.append(buff.getvalue()) # na posição [0] : vetor de bytes para mandar para a API da clarifai
    response.append(new_image_string) # na posição [1] : string em base64 pra decodificar e voltar pra imagem
    
    return response

#Função que divide um nome de cor de acordo com suas letras maiúsculas
#---RETORNO: uma string com o nome da cor separado (espaço) pelas letras maiúsculas.
def separate_capital_letters(string):
    count = 0 # inicializa o contador que verifica a quantidade de letras maiusculas
    string_list = list(string) # transforma a palavra passada em um vetor de char
    capitalLetters = [] # inicializa o vetor que vai conter apenas as letras maiusculas
    flag_translate = True
    
    # percorre todos os chars da string passada
    for letter in string_list:
        # caso a letra seja maiscula aumenta o contador e adiciona no vetor de letras maiusculas
        if(letter.isupper()):
            count = count + 1
            capitalLetters.append(letter)    

    # caso haja mais de uma letra maiuscula adiciona um espaço antes da letra para dar o espaçamento
    if(count > 1):
        flag_translate = False
        for capital in capitalLetters:
            letterIndex = string.find(capital)
            string_list[letterIndex] = ' ' + string_list[letterIndex]

    if(flag_translate == True):        
        # se for uma string com nome de uma cor única, retorna a string traduzida
        return sample_translate_text(string)
    else:
        # se for uma string com dois ou mais nomes de cores, retorna a string junta novamente e agora com os espaços
        return ''.join(string_list)
        #colorJoined = ''.join(string_list)
        #wordsSeparated = colorJoined.split(' ')
        
        #for word in wordsSeparated:
        #    word = sample_translate_text(word)
            
        #return ' '.joing(wordsSeparated)

#Função que traduz uma unica palavra passada
#---RETORNO: a palavra traduzida (string).
def sample_translate_text(text):
    client = translate.TranslationServiceClient()
    
    target_language = 'pt' # lingua desejada pra tradução
    
    # credencial para a API
    project_id = 'projeto-tcc-276919'    
    parent = client.location_path(project_id, "global")
    
    contents = [text]
    
    # Chama a requisição à API e pega sua resposta
    response = client.translate_text(
        parent=parent,
        contents=contents,
        mime_type='text/plain',
        source_language_code='en-US', # o atual idioma da palavra
        target_language_code=target_language)    

    #for translation in response.translations:
    #    print(u"Translated text: {}".format(translation.translated_text))
    
    # retorna apenas o primeiro resultado do vetor pois é apenas para uma palavra
    return response.translations[0].translated_text
