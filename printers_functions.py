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

# Declaração da credencial para APIs do Google e instancia do client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="projeto-tcc-276919-afa464aedacb.json"
client = vision.ImageAnnotatorClient()

# Declaração e intancia de client da API da Clarifai
channel = ClarifaiChannel.get_json_channel()
stub = service_pb2_grpc.V2Stub(channel)

#Função que printa as imagens e nomes de todos os objetos previamente reconhecidos  
#---RETORNO: sem retorno.
def print_all_objects(objects):
    #pyplot.axis("off")
    
    for object_ in objects:
        print(object_[0]) #nome do objeto
        pyplot.figure() # pra printar variar imagens sem sobreescrever
        pyplot.imshow(object_[1]) #imagem do objeto

#Função que printa a imagem e nome do objeto passado 
#---RETORNO: sem retorno.
def print_object(object_infos):    
    print(object_infos[0]) #nome do objeto    
    pyplot.imshow(object_infos[1]) #imagem do objeto

#Função que printa os resultados da busca
#---RETORNO: sem retorno.
def print_result_search(result):    
    i = 0

    if result == "Sem resultado para a busca":
        print(result)

    else:
        while i < len(result):        
            print(result[i][0])
            print(result[i][1]) 
            print("\n")
            i = i + 1
