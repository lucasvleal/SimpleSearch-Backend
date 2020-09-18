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

from aux_functions import separate_capital_letters

import settings

# Declaração da credencial para APIs do Google e instancia do client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="projeto-tcc-276919-afa464aedacb.json"
client = vision.ImageAnnotatorClient()

# Declaração e intancia de client da API da Clarifai
channel = ClarifaiChannel.get_json_channel()
stub = service_pb2_grpc.V2Stub(channel)

#Função que reconhece logos de empresas conhecidas da imagem passada
#---RETORNO: informações sobre a logo, nome e percentual de chance de ser.
def get_logos(content):
    # carrega a imagem para a memória
    # with io.open(path, 'rb') as image_file:
        # content = image_file.read()

    image = types.Image(content=content) # define o model da imagem

    # Chama a requisição à API e pega sua resposta
    response = client.logo_detection(image=image)
    logos = response.logo_annotations
    
    #print('Logos:')
    #for logo in logos:
    #    print(logo.description)

    # Reporta caso haja algum erro
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    
    if len(logos) > 0:
        if(logos[0].score > 0.90):
            # global logoGlobal
            settings.logoGlobal = logos[0].description        
            
        return logos    
    else:
        return False

#Função que pega as cores da imagem binaria do objeto passada
#---RETORNO: um vetor com as informações das cores na imagem do objeto.
def get_colors_image(file_bytes):
    # Monta a requisição à API, com o model desejado e a imagem passada
    request = service_pb2.PostModelOutputsRequest(
        model_id='eeed0b6733a644cea07cf4c60f87ebb7',
        inputs=[
          resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))
        ])
    
    # Instancia as credenciais 
    metadata = (('authorization', 'Key 4d258b07c14f429eb34dee874f24b69e'),)

    # Chama a requisição à API e pega sua resposta
    response = stub.PostModelOutputs(request, metadata=metadata)

    if response.status.code != status_code_pb2.SUCCESS:
      raise Exception("Request failed, status code: " + str(response.status.code))
    
    # Monta um array com as informações necessarias das cores encontradas na imagem do objeto
    all_infos = [] # inicializa o vetor que vai conter as infos de todas as cores

    # percorre o vetor de resposta da API com as informações das cores
    for color in response.outputs[0].data.colors:
        infos_color = [] # inicializa o vetor que vai conter as infos de uma cor apenas

        # adiciona as infos no vetor da cor
        infos_color.append(color.w3c.name)
        infos_color.append(color.w3c.hex)
        infos_color.append(color.value)

        #adiciona o vetor no vetor de todas as cores
        all_infos.append(infos_color)    
    
    return all_infos

#Função que pega possíveis textos presentes na imagem do objeto passada
#---RETORNO: um vetor com os textos na imagem do objeto.
def get_text(content):
    #Detects text in the file.
    # with io.open(path, 'rb') as image_file:
    #     content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    # print('Texts:')
    # for text in texts:
    #     print('\n"{}"'.format(text.description))

    #     vertices = (['({},{})'.format(vertex.x, vertex.y)
    #                 for vertex in text.bounding_poly.vertices])

    #     print('bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    justOne = []
    moreThanOne = []
    
    for text in texts:
        textFormatted = text.description.replace("\n", " ")
        splitted = textFormatted.split(" ")
        
        if len(splitted) > 1:
            moreThanOne.append(textFormatted.lower())
        else:
            justOne.append(textFormatted.lower())
    
    # print(justOne)
    # print(moreThanOne)

    if len(texts) > 0:
        # global textsGlobal
        settings.textsGlobal = justOne        
        return justOne
    
    else:
        return False

#Função que seleciona as cores principais presentes na imagem através de um vetor de cores passado
#---RETORNO: um vetor com o nome das principais cores.
def get_principal_colors(sorted_all):
    principal_colors = [] # inicializa o vetor que vai conter no máximo 3 cores principais
    principal_colors.append(sorted_all[0][2]) # adiciona a imagem com maior percentual de presença no vetor
    count = 0 # contador que auxiliara para o print

    # se a primeira cor tiver menos que 85% de presença na imagem ele adiciona a segunda cor que mais aparece
    if(principal_colors[0] < 0.85):
        principal_colors.append(sorted_all[1][2])
        count = count + 1

        # se a soma da primeira e segunda cores tiver menos que 98% de presença na imagem ele adiciona a terceira cor
        if((principal_colors[0] + principal_colors[1]) < 0.98):
            principal_colors.append(sorted_all[2][2])
            count = count + 1

    #print(principal_colors)
    #print(object_chosen[0] + " com as cores: \n")

    i = 0
    colors_names = []
    while(i <= count):
        in_percent = sorted_all[i][2] * 100.0
        #print(separate_capital_letters(sorted_all[i][0]) + " - " + str(in_percent) + "%")
        colors_names.append(separate_capital_letters(sorted_all[i][0]))
        i = i + 1
    
    return colors_names
