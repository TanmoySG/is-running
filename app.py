import json
from datetime import datetime
import shortuuid
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from os import path, write
from flask_cors import CORS
import requests
import smtplib
import ssl
import time
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

CORS(app)

file = "list.json"


class Get_Credentials:
    def __init__(self):
        self.server_credentials = json.load(open('server-config.json'))
        self.port = self.server_credentials['port']
        self.serverAddress = self.server_credentials['mail-server']
        self.sender = self.server_credentials['sender']
        self.password = self.server_credentials['password']


def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def alert(recipient, mail_template, content):
    credentials = Get_Credentials()
    message = MIMEMultipart("alternative")
    message["Subject"] = content["subject"]
    message["From"] = credentials.sender
    message["To"] = recipient
    template = open(mail_template).read()
    # .replace(content["replacement_token"], content["replacement_string"])
    for token in content["replacement_config"].keys():
        template = template.replace(str(token), str(
            content["replacement_config"][token]))
    html = MIMEText(template, "html")
    message.attach(html)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(credentials.serverAddress, credentials.port, context=context) as server:
        server.login(credentials.sender, credentials.password)
        server.sendmail(credentials.sender, recipient, message.as_string())
    return "Success"


def check_endpoint(endpoint, recipients=None):
    request_val = requests.get(endpoint, allow_redirects=True)
    response = {"status": "", "duration": "", "response": "", "redirects": []}
    if 100 <= int(request_val.status_code) <= 399:
        if request_val.history:
            response["duration"] = request_val.elapsed.total_seconds()
            response["status"] = str(request_val.status_code)
            response["response"] = "Success/Redirected"
            for history in request_val.history:
                response["redirects"].append(str(history.url))
        else:
            response["duration"] = request_val.elapsed.total_seconds()
            response["status"] = str(request_val.status_code)
            response["response"] = "Success"
            response["redirects"] = response["redirects"].append("None")
    elif 400 <= int(request_val.status_code) <= 499:
        response["duration"] = request_val.elapsed.total_seconds()
        response["status"] = str(request_val.status_code)
        response["response"] = "Bad Request"
        response["redirects"] = response["redirects"].append("None")

        if recipients != None:
            for recipient in recipients:
                content = {
                    "subject": "Alert | "+endpoint+" is Down.",
                    "replacement_config": {
                        "%url%": endpoint,
                        "%stscde%": str(response["status"]),
                        "%stsrsp%": str(response["response"]),
                        "%timestamp%": str(datetime.now()),
                    }
                }
                alert(recipient=recipient,
                      mail_template="./mail_templates/critical_alert_mail.txt", content=content)
            return response
        else:
            return response
    elif 500 <= int(request_val.status_code) <= 599:
        response["duration"] = request_val.elapsed.total_seconds()
        response["status"] = str(request_val.status_code)
        response["response"] = "Server Issue"
        response["redirects"] = response["redirects"].append("None")

        if recipients != None:
            for recipient in recipients:
                content = {
                    "subject": "Alert | "+endpoint+" is Down.",
                    "replacement_config": {
                        "%url%": endpoint,
                        "%stscde%": str(response["status"]),
                        "%stsrsp%": str(response["response"]),
                        "%timestamp%": str(datetime.now()),
                    }
                }
                alert(recipient=recipient,
                      mail_template="./mail_templates/critical_alert_mail.txt", content=content)
            return response
        else:
            return response

    return response


def generate_report(response):
    return {
        "timestamp": str(datetime.now()),
        "status": response['status'],
        "running": "Running" if 100 <= int(response['status']) <= 399 else "Downtime",
        "response": response['response'],
        "response-time": response['duration'],
        "redirects": response['redirects']
    }


@app.route("/<mail>/add/endpoint", methods=["GET", "POST"])
def add_endpoint(mail):
    new_ep_config = request.get_json(force=True)
    new_endpoint = new_ep_config['endpoint']
    password = new_ep_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            if new_endpoint not in endpoints.keys():
                endpoint_config = {
                    "endpoint": new_endpoint,
                    "endpoint-name": new_ep_config['name'],
                    "description": new_ep_config['description'],
                    "_id": shortuuid.uuid(),
                    "mail-list": [],
                    "status": "",
                    "running": "",
                    "last-check-timestamp": "",
                    "response": "",
                    "routine": new_ep_config['routine'],
                    "reports": []
                }
                check_result = check_endpoint(
                    endpoint=new_endpoint, recipients=new_ep_config['recipients'])
                report = generate_report(check_result)
                endpoint_config["status"] = report["status"]
                endpoint_config["running"] = report["running"]
                endpoint_config["last-check-timestamp"] = report["timestamp"]
                endpoint_config["response"] = report["response"]
                endpoint_config["reports"].append(report)
                for mail_address in new_ep_config['recipients']:
                    endpoint_config["mail-list"].append(mail_address)
                endpoints[new_endpoint] = endpoint_config
                write_json(jfile, file)
                for mail_address in new_ep_config['recipients']:
                    content = {
                        "subject": "Added to Critical Alerts Group",
                        "replacement_config": {
                            "%url%": new_endpoint,
                            "%reciever%": mail_address
                        }
                    }
                    alert(recipient=mail_address,
                          mail_template="./mail_templates/alert_onboarding_mail.txt", content=content)
                return "<h1>New Endpoint Added</h1>"
            else:
                return "<h1>Endpoint Exists</h1>"
        else:
            return "Doesnt Match"

    # endpoint = request.args.get('endpoint')


@app.route("/")
def index():
    return "<h1>It Fucking Works!</h1>"


@app.route("/<mail>/routine-check/", methods=["GET", "POST"])
def routine_check(mail):
    routine_check_config = request.get_json(force=True)
    current_hour = routine_check_config['current_hour']
    password = routine_check_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            if current_hour in ["3", "9", "15", "21"]:
                for endpoint in endpoints.keys():
                    check_result = check_endpoint(
                        endpoint=endpoint, recipients=endpoints[endpoint]['mail-list'])
                    report = generate_report(check_result)
                    endpoints[endpoint]["status"] = report["status"]
                    endpoints[endpoint]["running"] = report["running"]
                    endpoints[endpoint]["last-check-timestamp"] = report["timestamp"]
                    endpoints[endpoint]["response"] = report["response"]
                    if len(endpoints[endpoint]["reports"]) <= 10:
                        endpoints[endpoint]["reports"].append(report)
                    else:
                        endpoints[endpoint]["reports"].pop(index=0)
                        endpoints[endpoint]["reports"].append(report)
                write_json(jfile, file)
            else:
                return "job_scheduled_later"
        else:
            return "check_format"


@app.route("/<mail>/check-all/", methods=["GET", "POST"])
def bulk_check(mail):
    routine_check_config = request.get_json(force=True)
    password = routine_check_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            for endpoint in endpoints.keys():
                check_result = check_endpoint(
                    endpoint=endpoint, recipients=endpoints[endpoint]['mail-list'])
                report = generate_report(check_result)
                endpoints[endpoint]["status"] = report["status"]
                endpoints[endpoint]["running"] = report["running"]
                endpoints[endpoint]["last-check-timestamp"] = report["timestamp"]
                endpoints[endpoint]["response"] = report["response"]
                if len(endpoints[endpoint]["reports"]) <= 10:
                    endpoints[endpoint]["reports"].append(report)
                else:
                    endpoints[endpoint]["reports"].pop(0)
                    endpoints[endpoint]["reports"].append(report)
            write_json(jfile, file)
            return "bulk_check_success"
        else:
            return "credential_error"



@app.route("/check-one", methods=["GET"])
def get_endpoint():
    endpoint = request.args.get('endpoint')
    return str(check_endpoint(endpoint))


if __name__ == '__main__':
    app.run(debug=True)
