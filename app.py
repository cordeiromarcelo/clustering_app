from flask import Flask, render_template, request, redirect, url_for
import os
import json
import pandas as pd
import plotly
import plotly.express as px
from source import clustering
from os.path import join, dirname, realpath

app = Flask(__name__)

app.debug = True

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
    return redirect(url_for('renderTable', filename=uploaded_file.filename,
                            lat_col=request.values['lat'], long_col=request.values['long'],
                            peso_col=request.values['peso']))


@app.route('/<string:filename>/')
def renderTable(filename):
    lat_col = request.args.get('lat_col', None)
    long_col = request.args.get('long_col', None)
    peso_col = request.args.get('peso_col', None)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path, encoding='unicode_escape')
    df_clustered = clustering.create_clusters(df.copy(), lat_col, long_col, peso_col)

    px.set_mapbox_access_token('pk.eyJ1IjoiY29yZGVpcm9tYXJjZWxvIiwiYSI6ImNrb3RuM3J3NDBiNmIydm8xanpjdTdveXEifQ.9-X75KLPHqZGI-Ng_GYqJA')

    # fig = px.scatter_mapbox(df,
    #                         lat=lat_col,
    #                         lon=long_col,
    #                         title='Distribuição dos pontos dimensionados com o peso',
    #                         size=peso_col,
    #                         size_max=40,
    #                         zoom=3,
    #                         mapbox_style='outdoors',
    #                         height=700,
    #                         width=800
    #                         )
    #
    # graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    fig2 = px.scatter_mapbox(df_clustered,
                            lat=lat_col,
                            lon=long_col,
                            title='Cities Colored by Cluster (CDs acting area)',
                            #hover_name='city-state',
                            zoom=3,
                            mapbox_style='outdoors',
                            height=700,
                            width=800,
                            color='cluster'
                            )
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("table.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                           graphJSON=graphJSON2, zip=zip, len=len)




if __name__ == '__main__':
    app.run(debug=True)
