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

from principal_functions import get_infos_and_query
from aux_functions import base64_to_image

import settings

# Declaração da credencial para APIs do Google e instancia do client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="projeto-tcc-276919-afa464aedacb.json"
client = vision.ImageAnnotatorClient()

# Declaração e intancia de client da API da Clarifai
channel = ClarifaiChannel.get_json_channel()
stub = service_pb2_grpc.V2Stub(channel)

#Função que 'recorta' um objeto escolhido pelo seu nome a partir do reconhecimento previo dos objetos da imagem passada 
#---RETORNO: a imagem original recortada contendo apenas o objeto.
def cut_only_object(objects, object_name, im):
    # inicia os vertices que serao utilizados como limite para o recorte
    xl = 0 # limite esquerdo
    xr = 0 # limite direito
    yt = 0 # limite superior
    yb = 0 # limite inferior
    
    # percorre o array de objetos e verifica qual tem o nome igual o passado
    for object_ in objects:
        # quando achar um que contenha o nome igual salva os limites (vertices normalizados) para recorte
        if(object_.name == object_name):       
            xl = object_.bounding_poly.normalized_vertices[0].x
            xr = object_.bounding_poly.normalized_vertices[1].x
            yb = object_.bounding_poly.normalized_vertices[0].y
            yt = object_.bounding_poly.normalized_vertices[2].y
    
    height = im.shape[0] # pega a altura da imagem
    width = im.shape[1] # pega a largura da imagem
    
    # faz o processo inverso da normalização dos vertices
    vert_left = int(xl * width) 
    vert_right = int(xr * width)
    vert_top = int(yt * height)
    vert_bottom = int(yb * height)    
    
    img_pb = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); # converte a imagem para escala de cinza para melhor resultado do recorte
    img_crop = img_pb[vert_bottom:vert_top, vert_left:vert_right] # recorta a imagem de um limite para o outro nos 2 eixos  
    
    #pyplot.imshow(img_crop)
    
    return cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB)

#Função que retorna um dos objetos de todos previamente reconhecidos a partir do seu nome
#---RETORNO: o vetor com a query gerada [1] e a imagem [0] do objeto.
def choose_object(objects, name):
	settings.init()
	# print("objeto: ", name)

	# percorre o array de objetos reconhecidos e seleciona o que tem nome igual o passado
	for object_ in objects:
		# print("nome objeto iteracao: ", object_[0])

		object_[1] = base64_to_image(object_[1])
		if(object_[0] == name):
			query = get_infos_and_query(object_)
			return [object_, query]

#Função que adiciona à query templates que otimizam a busca no motor de busca
#---RETORNO: a query final com o template.
def include_template(query, name):
    nameSplitted = name.split(" ")
    name = name.lower()
    finalQuery = "intitle:" + name + " "
    
    colors = []
    
    firstTextPosition = len(query)
    
    if settings.textsGlobal != False:
        firstTextPosition = query.index(settings.textsGlobal[0])
    
    aux = 0
    while aux < firstTextPosition:
        if query[aux] not in nameSplitted:            
            if query[aux] != settings.logoGlobal:
                colors.append(query[aux])
        aux += 1
                
    # for word in query:
        # if word not in nameSplitted:            
            # if word != logoGlobal:
                # colors.append(word)
          

    #print(colors)

    sizeColors = len(colors)
    i = 0
    
    while(i < sizeColors):
        finalQuery += colors[i] + " "
        
        if i+1 != sizeColors:
            finalQuery += "intitle:" + name + " " # OR 
            
        i += 1    
    
    if settings.logoGlobal != False:
        finalQuery += '"' + settings.logoGlobal
        
        if settings.textsGlobal != False:
            for text in settings.textsGlobal:
                if text != settings.logoGlobal and text != settings.logoGlobal.lower():
                    finalQuery += " " + text
                
            finalQuery += '"'
        else:
            finalQuery += '"'
                
    return finalQuery

#Função que melhora a query para a busca no motor de busca
#---RETORNO: a query melhorada.
def adapt_query(query, name):
    colorsToChange = ["cinzento", "gray", "grey", "blue", "green", "red", "vermelho", "yellow", "orange", "purple", "branco", "preto", "white", "black"]
    colorsChanged = ["cinza", "azul", "verde", "vermelho", "amarelo", "laranja", "roxo", "branco", "preto"]
    colorsToMantain = ["salmão", "coral", "vinho", "bordô", "rosa", "ciano", "magenta"]
    
    shineToChange = ["steel", "bronzeado", "silver", "prata", "gold", "dourado"]
    shineChanged = ["metálico", "prata", "dourado"]
    
    lightnessToChange = ["light", "dark"]
    lightnessChanged = ["claro", "escuro"]
    
    words = query.split() 
    size = len(words)    
    
    nameSplitted = name.split(" ")
    nameSize = len(nameSplitted)
    
    separatedWords = []    
    i = 0 
    
    for word in words:
        formattedWord = word.lower()
        priority = 0
        infosWord = []
        
        if formattedWord in colorsToChange:           
            if formattedWord == 'cinzento' or formattedWord == 'cinzenta' or formattedWord == 'gray' or formattedWord == 'grey':
                word = colorsChanged[0]
            elif formattedWord == 'blue':
                word = colorsChanged[1]
            elif formattedWord == 'green':
                word = colorsChanged[2]
            elif formattedWord == 'red' or formattedWord == 'vermelho' or formattedWord == 'vermelha':
                word = colorsChanged[3]
            elif formattedWord == 'yellow':
                word = colorsChanged[4]
            elif formattedWord == 'orange':
                word = colorsChanged[5]
            elif formattedWord == 'purple':
                word = colorsChanged[6]
            elif formattedWord == 'white' or formattedWord == 'branco' or formattedWord == 'branca':
                word = colorsChanged[7]
            elif formattedWord == 'black' or formattedWord == 'preto' or formattedWord == 'preta':
                word = colorsChanged[8]
                
            priority = 3
            infosWord.append(word)
            infosWord.append(priority)
                
        elif formattedWord in shineToChange:
            if formattedWord == 'steel' or formattedWord == 'bronzeado':
                word = shineChanged[0]
            elif formattedWord == 'silver' or formattedWord == 'prata':
                word = shineChanged[1]   
            elif formattedWord == 'gold' or formattedWord == 'dourado':
                word = shineChanged[2] 
                
            priority = 2
            infosWord.append(word)
            infosWord.append(priority)
            
        elif formattedWord in lightnessToChange:
            if formattedWord == 'light':
                word = lightnessChanged[0]
            elif formattedWord == 'dark':
                word = lightnessChanged[1]           
                
            priority = 1
            infosWord.append(word)
            infosWord.append(priority)
        
        elif formattedWord == words[0].lower():
            priority = 4
            infosWord.append(word)
            infosWord.append(priority)
            
        elif settings.logoGlobal != False and formattedWord in settings.logoGlobal:
            priority = 0
            infosWord.append(word)
            infosWord.append(priority)
            
        elif settings.textsGlobal != False and formattedWord in settings.textsGlobal:
            priority = 0
            infosWord.append(word)
            infosWord.append(priority)
        
        elif formattedWord in nameSplitted:
            priority = 4
            infosWord.append(word)
            infosWord.append(priority)
            
        elif formattedWord in colorsToMantain:
            priority = 3
            infosWord.append(word)
            infosWord.append(priority)
            
        # Não sendo nem produto, nem logo, nem cores ou tons possíveis, seta o nome do produto, sendo retirado dps 
        else: 
            priority = 0
            infosWord.append(words[0])
            infosWord.append(priority)
            
        separatedWords.append(infosWord)
        words[i] = word
        i = i + 1
            
    ordered = sorted(separatedWords, key= lambda x: x[1], reverse=True)
    # print(ordered)
    
    auxOrder = 0    
    newList = []
    
    while auxOrder < size:
        words[auxOrder] = ordered[auxOrder][0]
        auxOrder = auxOrder + 1
    
    finalQuery = []
    for word in words:
        if word not in finalQuery:
            finalQuery.append(word)
            
    # queryChanged = ' '.join(finalQuery)
    
    finalQuery = include_template(finalQuery, name)
    
    return finalQuery
