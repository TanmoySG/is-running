from flask import Flask, request
import requests

app = Flask(__name__)


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
