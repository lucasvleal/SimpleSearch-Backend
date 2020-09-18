import os
import base64
from io import BytesIO
from flask import Flask, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def hello_world():
	if request.method == 'POST':
		username = request.get_json()		
		return 'Hello, %s!' % username['username']
	else:
		return 'Hello, stranger!'

@app.route('/image', methods=['POST'])
def image():
	if request.method == 'POST':
		if 'image_test' not in request.files:
			flash('No file part')
			return redirect(request.url)

		test = request.files['image_test']
		print("imagem: ", test.filename)

		if test and allowed_file(test.filename):
			filename = secure_filename(test.filename)
			test.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

			with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "rb") as img:
				image_base64 = base64.b64encode(img.read()) # codifica a imagem em base64
				string_image_base64 = image_base64.decode("utf-8")
			
			return {
				"imageBase64": string_image_base64
			}
	else:
		return 'Image came here'

@app.route('/images/<filename>', methods=['GET','POST'])
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'],filename)