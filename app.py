import json
from typing import Collection
import shortuuid
import secrets
import random
import hashlib
from flask import Flask, request, jsonify, send_from_directory
import os.path
from os import path, write
from flask_cors import CORS
import requests

app = Flask(__name__)

CORS(app)

def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def alert(endpoint, response):
    


@app.route("/")
def index():
    return "<h1>It Fucking Works!</h1>"


def check(endpoint):
    response = requests.get(endpoint)
    return str(response.status_code)


@app.route("/check-one", methods=["GET"])
def get_endpoint():
    endpoint = request.args.get('endpoint')
    return check(endpoint)


if __name__ == '__main__':
    app.run(debug=True)
