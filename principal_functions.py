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

from terciary_functions import get_logos, get_text, get_colors_image, get_principal_colors
from aux_functions import image_to_base64_and_bin

import settings

# Declaração da credencial para APIs do Google e instancia do client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="projeto-tcc-276919-afa464aedacb.json"
client = vision.ImageAnnotatorClient()

# Declaração e intancia de client da API da Clarifai
channel = ClarifaiChannel.get_json_channel()
stub = service_pb2_grpc.V2Stub(channel)

#Função que localiza diversos objetos da imagem passada
#---RETORNO: informações sobre o objeto, a posição dele e limites retangulares para a região da imagem que o contém.
def localize_objects(content):
    # carrega a imagem para a memória
        # with open(path, 'rb') as image_file:
        #     content = image_file.read()
            
        image = types.Image(content=content) # define o model da imagem

        # Chama a requisição à API e pega sua resposta
        objects = client.object_localization(
            image=image,image_context={"language_hints": ["pt"]}).localized_object_annotations        
       
        #print('Number of objects found: {}'.format(len(objects)))     
                
        return objects

#Função que 'recorta' todos os objetos a partir do reconhecimento previo dos objetos da imagem passada 
#---RETORNO: um vetor com todos os objetos cortados [1] a partir da imagem original e seus nomes [0] em um vetor.
def cut_all_objects(objects, im):
    xl = 0 # limite esquerdo
    xr = 0 # limite direito
    yt = 0 # limite superior
    yb = 0 # limite inferior 
    all_objects = [] # inicialização do array que contara as imagens dos objetos
    
    height = im.shape[0] # pega a altura da imagem
    width = im.shape[1] # pega a largura da imagem
    
    # percorre o array de objetos reconhecidos e os recorta da imagem original
    for object_ in objects:
        object_info = [] # inicialização do vetor que vai ter a imagem e o nome do objeto
        xl = object_.bounding_poly.normalized_vertices[0].x
        xr = object_.bounding_poly.normalized_vertices[1].x
        yb = object_.bounding_poly.normalized_vertices[0].y
        yt = object_.bounding_poly.normalized_vertices[2].y
        
        # faz o processo inverso da normalização dos vertices
        vert_left = int(xl * width)
        vert_right = int(xr * width)
        vert_top = int(yt * height)
        vert_bottom = int(yb * height)
        
        # adiciona ao vetor do objeto seu nome traduzido
        name = sample_translate_text(object_.name)
        if name == "Topo":
            name = "Camiseta"
        object_info.append(name)
        #object_info.append(object_.name) # nome sem tradução
        
        # converte a imagem para escala de cinza para melhor resultado do recorte
        img_pb = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); 
        img_crop = im[vert_bottom:vert_top, vert_left:vert_right] # recorta a imagem de um limite para o outro nos eixos
        
        #img_rgb = cv2.cvtColor(img_crop, cv2.COLOR_GRAY2RGB)
        
        # adiciona ao vetor do objeto sua imagem
        image_done = cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB)
        image_stringfyed = image_to_base64_and_bin(image_done)[1]
        object_info.append(image_stringfyed)
        
        # adiciona o vetor do objeto ao vetor de todos os objetos
        all_objects.append(object_info) 
        
    return all_objects

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

#Função que integra as outras fuñções que pegam caracteristicas da imagem e gera a query
#---RETORNO: retorna a query obtida através das infos buscadas.
def get_infos_and_query(object_):
    bytes_base64 = image_to_base64_and_bin(object_[1]) # função que realiza a conversão para binario e base64
    response = get_colors_image(bytes_base64[0]) # função que pega as cores da imagem do objeto
    sorted_all = sorted(response, key= lambda x: x[2], reverse=True)
    #print(sorted_all)
    logos = get_logos(bytes_base64[0]) # função que identifica logos na imagem
    texts = get_text(bytes_base64[0]) # função que identifica textos na imagem
    #print(object_[0] + " com as cores:")
    colors = get_principal_colors(sorted_all)
    
    #print(colors)
    
    query = object_[0]
    
    for color in colors :
        query += " " + color
    
    #verificar se o text é igual o logo e colocar os texts na query
    
    if settings.logoGlobal != False:
        if settings.logoGlobal.lower() not in texts:            
            query += " " + settings.logoGlobal    
      
    if texts != False:
        if len(texts) > 0:
            for text in texts:
                query += " " + text
    
    #searchResults = google_search(query, 4, api_key, cse_id)
    
    #return searchResults
    return query

#Função que busca a query passada no google e retorna as urls encontradas 
#---RETORNO: um vetor com as urls dos primeiros [qnt_responses] sites encontrados.
def google_search(search_term, qnt_responses, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    
    class Struct:
        def __init__(self, **entries):
            self.__dict__.update(entries)
    
    objectResult = Struct(**res)
    information = Struct(**objectResult.searchInformation)
    total = int(information.totalResults)
    
    i = 0
    response = []
    
    if total == 0:
        return "Sem resultado para a busca"
    
    if total < qnt_responses:
         while i < total:
            item = []
            itemClass = Struct(**objectResult.items[i])
            item.append(itemClass.title)
            item.append(itemClass.link)
            response.append(item)
            i = i + 1 
    
    else:        
        while i < qnt_responses:
            item = []
            itemClass = Struct(**objectResult.items[i])
            item.append(itemClass.title)
            item.append(itemClass.link)
            response.append(item)
            i = i + 1     
    
    return response
