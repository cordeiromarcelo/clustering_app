from flask import Flask, render_template, request, redirect, url_for
import os
import io
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    return redirect(url_for('renderTable', filename=uploaded_file.filename))


@app.route('/<string:filename>/',  methods=['GET', 'POST'])
def renderTable(filename):
    # get the uploaded file
    if request.method == 'GET':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(file_path, encoding='unicode_escape')
        return render_template("table.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                               zip=zip, len=len)
    else:
        return redirect(url_for('renderTableMap', filename=filename,
                            lat_col=request.values['lat'], long_col=request.values['long'],
                            peso_col=request.values['peso']))


@app.route('/<string:filename>/map/', methods=['GET', 'POST'])
def renderTableMap(filename):
    lat_col = request.args.get('lat_col', None)
    long_col = request.args.get('long_col', None)
    peso_col = request.args.get('peso_col', None)

    if request.method == 'GET':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(file_path, encoding='unicode_escape')

        countRows = len(df)
        uniques = len(df[[lat_col, long_col]].drop_duplicates())
        pesoInfo = dict(np.round(df[peso_col].describe()[['mean', 'min', 'max']], 1))

        px.set_mapbox_access_token('pk.eyJ1IjoiY29yZGVpcm9tYXJjZWxvIiwiYSI6ImNrb3RuM3J3NDBiNmIydm8xanpjdTdveXEifQ.9-X75KLPHqZGI-Ng_GYqJA')

        fig = px.scatter_mapbox(df,
                                lat=lat_col,
                                lon=long_col,
                                size=peso_col,
                                size_max=40,
                                zoom=3,
                                mapbox_style='outdoors',
                                height=700,
                                width=800
                                )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("tablemap.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                               graphJSON=graphJSON, zip=zip, len=len, countRows=countRows, uniques=uniques,
                               pesoInfo=pesoInfo)
    else:
        return redirect(url_for('renderTableClustered', filename=filename,
                                lat_col=lat_col, long_col=long_col,
                                peso_col=peso_col, clusters=request.values['clusters']))


@app.route('/<string:filename>/map/clustered/')
def renderTableClustered(filename):
    lat_col = request.args.get('lat_col', None)
    long_col = request.args.get('long_col', None)
    peso_col = request.args.get('peso_col', None)
    clusters = int(request.args.get('clusters', None))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path, encoding='unicode_escape')

    countRows = len(df)
    uniques = len(df[[lat_col, long_col]].drop_duplicates())
    pesoInfo = dict(np.round(df[peso_col].describe()[['mean', 'min', 'max']], 1))

    df_clustered = clustering.create_clusters(df.copy(), lat_col, long_col, peso_col, clusters)
    px.set_mapbox_access_token('pk.eyJ1IjoiY29yZGVpcm9tYXJjZWxvIiwiYSI6ImNrb3RuM3J3NDBiNmIydm8xanpjdTdveXEifQ.9-X75KLPHqZGI-Ng_GYqJA')

    fig_cluster = px.scatter_mapbox(df_clustered,
                            lat=lat_col,
                            lon=long_col,
                            #hover_name='city-state',
                            zoom=3,
                            mapbox_style='outdoors',
                            height=700,
                            width=800,
                            color='cluster'
                            )
    graphJSON_cluster = json.dumps(fig_cluster, cls=plotly.utils.PlotlyJSONEncoder)

    df_clustered_unique = df_clustered.drop_duplicates(['cluster_lat', 'cluster_lng'])
    fig_centers = px.scatter_mapbox(df_clustered_unique,
                            lat=lat_col,
                            lon=long_col,
                            zoom=3,
                            size=[30 for i in range(len(df_clustered_unique))],
                            size_max=30,
                            mapbox_style='outdoors',
                            height=700,
                            width=800,
                            color='cluster'
                            )

    graphJSON_centers = json.dumps(fig_centers, cls=plotly.utils.PlotlyJSONEncoder)

    fig, ax = plt.subplots(figsize=(14, 14))
    ax.scatter(df_clustered[long_col], df_clustered[lat_col], c=df_clustered['cluster'],
               s=df_clustered[peso_col] * 3)
    ax.scatter(df_clustered_unique['cluster_lng'], df_clustered_unique['cluster_lat'], marker='x', color='red', s=200)
    plt.title('Distribution Center Location ("x") and Cities ("O") sized by Delayed Orders')

    img = io.StringIO()
    fig.savefig(img, format='svg')
    # clip off the xml headers from the image
    svg_img = '<svg' + img.getvalue().split('<svg')[1]

    return render_template("tablecluster.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                           graphJSON_cluster=graphJSON_cluster, zip=zip, len=len, countRows=countRows, uniques=uniques,
                           pesoInfo=pesoInfo, graphJSON_centers=graphJSON_centers, svg_img=svg_img)


if __name__ == '__main__':
    app.run(debug=True)
