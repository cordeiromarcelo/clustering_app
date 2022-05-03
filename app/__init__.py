from flask import Flask, render_template
from app.geo_cluster.routes import geo_cluster as geo_cluster_module

app = Flask(__name__)

app.config.from_object('config')

app.register_blueprint(geo_cluster_module)