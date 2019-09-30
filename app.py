import os
from flask import Flask, flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
import glob
import uuid

app = Flask(__name__, static_folder = "./static", template_folder = "static")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
ALLOWED_EXTENSIONS = set(['mp3'])
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import essentia
import essentia.standard as es

def getUniquePath(folder, filename):
   path = os.path.join(folder, filename)
   while os.path.exists(path):
        path = path.split('.')[0] + ''.join(random.choice(string.ascii_lowercase) for i in range(10)) + '.' + path.split('.')[1]
   return path

def get_detection():
    files_path = os.path.join(app.config['UPLOAD_FOLDER'], '*')
    files = sorted(
        glob.iglob(files_path), key=os.path.getctime, reverse=True) 
    _file = os.path.join(app.config['UPLOAD_FOLDER'], files[0])
    features, features_frames = es.MusicExtractor(
            lowlevelStats=['mean', 'stdev'],
            rhythmStats=['mean', 'stdev'],
            tonalStats=['mean', 'stdev'])(_file)
    print("BPM:", features['rhythm.bpm'])
    print("Key/scale estimation (using a profile specifically suited for electronic music):",
        features['tonal.key_edma.key'], features['tonal.key_edma.scale'])
    
    return jsonify(
        bpm = features['rhythm.bpm'],
        key = features['tonal.key_edma.key'],
        scale = features['tonal.key_edma.scale']
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/get_analysis', methods=['GET'])
def get_analysis():
    return get_detection()

@app.route('/api/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return 'Welcome to upload'
    if request.method == 'POST':
        target = app.config['UPLOAD_FOLDER']
        if not os.path.isdir(target):
            os.makedirs(target)

        try:
            _file = request.files['files']

            if 'files' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            if _file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if _file and allowed_file(_file.filename):
                filename = secure_filename(_file.filename)

                _file_url = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()) + '_' + filename)
                _file.save(_file_url)
                return jsonify({'ok': True, 'message': 'File uploaded successfully!'}), 200
            else:
                return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400

        except Exception as e:
            return(str(e))

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found"

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run()