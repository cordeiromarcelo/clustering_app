from flask import Flask, render_template, request, redirect, url_for
import os
from os.path import join, dirname, realpath
from source import parser

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/", methods=['POST'])
def uploadFiles():
    # get the uploaded file
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # set the file path
        uploaded_file.save(file_path)
          # save the file
    return redirect(url_for('renderTable', filename=uploaded_file.filename))


@app.route('/<string:filename>/')
def renderTable(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = parser.parseCSV(file_path)
    return render_template("table.html", column_names=df.columns.values, row_data=list(df.values.tolist()),
                           link_column="first_name", zip=zip)

if __name__ == '__main__':
    app.run(debug=True)
