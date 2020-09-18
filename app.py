import os
import base64
import cv2

from io import BytesIO
from flask import Flask, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

from principal_functions import localize_objects, cut_all_objects, google_search
from secundary_functions import adapt_query, choose_object
from terciary_functions import get_text
from aux_functions import base64_to_image
from printers_functions import print_result_search

# import keys
import keys
api_key = keys.api
cse_id = keys.cse

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def hello_user():
	return 'Hello, user! To begin use SimpleSearch send some image to /initial-image :)'
	
@app.route('/initial-image', methods=['POST'])
def initial_image():
	if request.method == 'POST':
		if 'image' not in request.files:
			flash('No file part')
			return redirect(request.url)

		initial = request.files['image']
		# print("imagem: ", initial.filename)

		if initial and allowed_file(initial.filename):
			filename = secure_filename(initial.filename)
			path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			initial.save(path)

			with open(path, "rb") as img:
				content = img.read()
				
			img = cv2.imread(path) # leitura da imagem com openCV -> retorna um numpy array			

			returned_objects = localize_objects(content)
			all_objects = cut_all_objects(returned_objects, img)			
			
			return {
				"allObjects": all_objects
			}
	else:
		return 'Image came here'

@app.route('/object-image', methods=['POST'])
def image():
	if request.method == 'POST':		
		json = request.get_json()		
		# print("json: ", json)

		if json:
			all_objects = json['allObjects']

			name = json['choosenObject']  # nome do objeto

			# chama a função que escolhe o vetor de informações do objeto
			object_chosen = choose_object(all_objects, name)

			queryToSearch = adapt_query(object_chosen[1], name)

			result = google_search(queryToSearch, 5, api_key, cse_id)
			
			return {
				"resultsSearch": result
			}
	else:
		return 'Nâo veio JSON'

@app.route('/images/<filename>', methods=['GET','POST'])
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

if __name__ == '__main__':
	app.run()