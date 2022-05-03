from flask import Blueprint, render_template, request, redirect, url_for
import os
import io
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
from app.source import clustering
import config

geo_cluster = Blueprint('geo_cluster', __name__, url_prefix='/')

@geo_cluster.route('/')
def index():
    return render_template('geo_cluster/index.html')

@geo_cluster.route("/", methods=['POST'])
def uploadFiles():
    # get the uploaded file
    uploaded_file = request.files['file']

    if uploaded_file.filename != '':
        file_path = os.path.join(config.UPLOAD_FOLDER, uploaded_file.filename)
        # set the file path
        uploaded_file.save(file_path)
        # save the file
    return redirect(url_for('geo_cluster.renderTable', filename=uploaded_file.filename))


@geo_cluster.route('/<string:filename>/',  methods=['GET', 'POST'])
def renderTable(filename):
    # get the uploaded file
    if request.method == 'GET':
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
        df = pd.read_csv(file_path, encoding='unicode_escape')
        return render_template("geo_cluster/table.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                               zip=zip, len=len)
    else:
        return redirect(url_for('geo_cluster.renderTableMap', filename=filename,
                            lat_col=request.values['lat'], long_col=request.values['long'],
                            peso_col=request.values['peso']))


@geo_cluster.route('/<string:filename>/map/', methods=['GET', 'POST'])
def renderTableMap(filename):
    lat_col = request.args.get('lat_col', None)
    long_col = request.args.get('long_col', None)
    peso_col = request.args.get('peso_col', None)

    if request.method == 'GET':
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
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

        return render_template("geo_cluster/tablemap.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                               graphJSON=graphJSON, zip=zip, len=len, countRows=countRows, uniques=uniques,
                               pesoInfo=pesoInfo)
    else:
        return redirect(url_for('geo_cluster.renderTableClustered', filename=filename,
                                lat_col=lat_col, long_col=long_col,
                                peso_col=peso_col, clusters=request.values['clusters']))


@geo_cluster.route('/<string:filename>/map/clustered/')
def renderTableClustered(filename):
    lat_col = request.args.get('lat_col', None)
    long_col = request.args.get('long_col', None)
    peso_col = request.args.get('peso_col', None)
    clusters = int(request.args.get('clusters', None))

    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
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
                            lat='cluster_lat',
                            lon='cluster_lng',
                            zoom=3,
                            size=[30 for i in range(len(df_clustered_unique))],
                            size_max=30,
                            mapbox_style='outdoors',
                            height=700,
                            width=800,
                            color='cluster'
                            )

    graphJSON_centers = json.dumps(fig_centers, cls=plotly.utils.PlotlyJSONEncoder)

    json_result_string = df_clustered_unique.to_json(
        orient='records',
        double_precision=12,
        date_format='iso'
    )
    json_result = json.loads(json_result_string)

    geo_json = {
        'type': 'FeatureCollection',
        'features': []
    }
    for record in json_result:
        geo_json['features'].append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [record['cluster_lng'], record['cluster_lat']],
            },
            'properties': record,
        })

    #geo_json = json.dumps(geo_json, indent=2)

    return render_template("geo_cluster/tablecluster.html", column_names=df.columns.values, row_data=list(df.values.tolist())[:10],
                           graphJSON_cluster=graphJSON_cluster, zip=zip, len=len, countRows=countRows, uniques=uniques,
                           pesoInfo=pesoInfo, graphJSON_centers=graphJSON_centers, geo_json=geo_json)