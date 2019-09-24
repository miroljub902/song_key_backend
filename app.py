import os
from flask import Flask, flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename


app = Flask(__name__, static_folder = "./static", template_folder = "static")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
ALLOWED_EXTENSIONS = set(['mp3'])
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import essentia
import essentia.standard as es

def get_detection():
    _file = os.path.join(app.config['UPLOAD_FOLDER'], '1.mp3')
    features, features_frames = es.MusicExtractor(
            lowlevelStats=['mean', 'stdev'],
            rhythmStats=['mean', 'stdev'],
            tonalStats=['mean', 'stdev'])(_file)
    print("BPM:", features['rhythm.bpm'])
    print("Key/scale estimation (using a profile specifically suited for electronic music):",
        features['tonal.key_edma.key'], features['tonal.key_edma.scale'])
    
    return jsonify(
        bpm = features['rhythm.bpm'],
        key = features['tonal.key_edma.scale']
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/get_analysis', methods=['GET'])
def get_analysis():
    return get_detection()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            return 'successfully uploaded'
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    app.run()