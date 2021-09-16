import json
from datetime import datetime, date
import shortuuid
import hashlib
import smtplib
import ssl
import os
import requests
from flask import Flask, request
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


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


def mail_report(attachment, recipient, content):
    mail_template = "./mail_templates/report_mail.txt"
    credentials = Get_Credentials()
    message = MIMEMultipart("alternative")
    message["Subject"] = content["subject"]
    message["From"] = credentials.sender
    message["To"] = recipient
    template = open(mail_template).read().replace(
        "%reptype%", content["report_type"])
    template = template.replace(
        "%epurl%", content["ep"])
    html = MIMEText(template, "html")
    message.attach(html)
    # Attachement
    try:
        with open("./reports/"+attachment, "rb") as att:
            p = MIMEApplication(att.read(), _subtype="txt")
            p.add_header('Content-Disposition',
                         "attachment", filename=attachment)
            message.attach(p)
    except Exception as e:
        print(str(e))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(credentials.serverAddress, credentials.port, context=context) as server:
        server.login(credentials.sender, credentials.password)
        server.sendmail(credentials.sender, recipient, message.as_string())
    return "report_sent"


def generate_cumulative_report(report_config_flag="all"):
    with open('list.json') as f:
        jfile = json.load(f)
        # user_cred = jfile['user']
        endpoints = jfile['endpoints']
        if report_config_flag == "all":
            template = open(
                "./report_templates/overall_report_template.txt").read()
            for endpoint in endpoints:
                rep_sum = "\n|  Endpoint : %endpoint% [ %epname% - %schedule% ]\n======================================================================================"
                content = endpoints[endpoint]
                rep_sum = rep_sum.replace("%endpoint%", content['endpoint'])
                rep_sum = rep_sum.replace(
                    "%epname%", content['endpoint-name'])
                rep_sum = rep_sum.replace(
                    "%schedule%", content['routine']+" Hrs")
                for indv_rep in content['reports']:
                    rep_sum = rep_sum+"\n|  "+str(indv_rep['timestamp'])+"  |  "+str(indv_rep['running'])+"  |  " + \
                        str(indv_rep['status'])+"  |  "+str(indv_rep['response']) + \
                        "  |  "+str(indv_rep['response-time']) + \
                        "  |  "
                    if indv_rep['redirects'] != None:
                        rep_sum = rep_sum + " -> ".join(indv_rep['redirects'])
                    else:
                        rep_sum = rep_sum + "No Redirects"
                template = template+rep_sum
                template = template + \
                    "\n======================================================================================"
            rep_save = open("./reports/"+str(date.today()) +
                            "-cumulative-report.txt", "w+")
            rep_save.write(template)
            rep_save.close
            return str(date.today())+"-cumulative-report.txt"
        else:
            template = open(
                "./report_templates/individual_report_template.txt").read()
            content = endpoints[report_config_flag]
            template = template.replace("%endpoint%", content['endpoint'])
            template = template.replace("%epname%", content['endpoint-name'])
            template = template.replace("%epdesc%", content['description'])
            template = template.replace("%status%", content['running'])
            template = template.replace("%stscde%", content['status'])
            template = template.replace("%stsrsp%", content['response'])
            template = template.replace(
                "%tmstmp%", content['last-check-timestamp'])
            template = template.replace(
                "%schedule%", "Every "+content['routine']+" Hrs")
            rep_sum = ""
            for indv_rep in content['reports']:
                rep_sum = rep_sum+"\n|  "+str(indv_rep['timestamp'])+"  |  "+str(indv_rep['running'])+"  |  " + \
                    str(indv_rep['status'])+"  |  "+str(indv_rep['response']) + \
                    "  |  "+str(indv_rep['response-time'])+"  |"

            template = template+rep_sum
            rep_save = open("./reports/"+content['_id']+".txt", "w+")
            rep_save.write(template)
            rep_save.close
            return content['_id']+".txt"


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


def format_report(response):
    return {
        "timestamp": str(datetime.now()),
        "status": response['status'],
        "running": "Running" if 100 <= int(response['status']) <= 399 else "Downtime",
        "response": response['response'],
        "response-time": response['duration'],
        "redirects": response['redirects']
    }


# Endpoints #########

# Add Endpoint to In-system EP Library for check - /<mail>/add/endpoint
# <mail> - Admin Email
# Payload : {
#  "endpoint":<ep-to-add> ,
#  "password": <admin-password>,
#  "name": <nickname for ep>,
#  "description": <description-of-ep>,
#  "recipients": [<recipient1-mail>, <recipient2-mail>],
#  "routine" : <routine-check-schedule-in-hrs : 6/12/24>
# }
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
                report = format_report(check_result)
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


# Delete In-system Endpoint - /<mail>/delete/endpoint
# <mail> - Admin Email
# Payload : {
#              password: <admin-password>,
#              endpoint : <URL>
#           }

@app.route("/<mail>/delete/endpoint", methods=["GET", "POST"])
def delete_endpoint(mail):
    new_ep_config = request.get_json(force=True)
    endpoint = new_ep_config['endpoint']
    password = new_ep_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            if endpoint in endpoints.keys():
                endpoints.pop(endpoint)
                write_json(jfile, file)
                return "ep_deleted"
            else:
                return "ep_does_not_exist"
        else:
            return "credential_mismatch"


# Check In-system Endpoint on Demand - /<mail>/check/endpoint
# <mail> - Admin Email
# Payload : {
#              password: <admin-password>,
#              endpoint : <URL>
#           }


@app.route("/<mail>/check/endpoint", methods=["GET"])
def standalone_ep_check(mail):
    status_config = request.get_json(force=True)
    password = status_config['password']
    endpoint = status_config['endpoint']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            if endpoint in endpoints.keys():
                check_result = check_endpoint(
                    endpoint=endpoint, recipients=endpoints[endpoint]['mail-list'])
                report = format_report(check_result)
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
            else:
                return "endpoint_not_found"
        else:
            return "credential_error"


# Initial EP - /

@app.route("/")
def index():
    return "<h1>It Fucking Works!</h1>"


@app.route("/<mail>/login")
def login(mail):
    password = request.get_json(force=True)['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash and mail == user_cred['email'] :
            return user_cred
        else:
            return "credential_error"


# Routine Check Endpoints - /<mail>/routine-check/<token>/<slots>
# <mail> - Admin Email
# <token> - access token
# <slots> - 6-12-24 / 6 / 6-12
# For internal Jobs (CRON Calls) only

@app.route("/<mail>/routine-check/<token>/<slots>", methods=["GET", "POST"])
def routine_check(mail, token, slots):
    current_slots = slots.split("-")
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        if user_cred['token'] == token and user_cred['email'] == mail:
            for endpoint in endpoints.keys():
                if endpoints[endpoint]['routine'] in current_slots:
                    check_result = check_endpoint(
                        endpoint=endpoint, recipients=endpoints[endpoint]['mail-list'])
                    report = format_report(check_result)
                    endpoints[endpoint]["status"] = report["status"]
                    endpoints[endpoint]["running"] = report["running"]
                    endpoints[endpoint]["last-check-timestamp"] = report["timestamp"]
                    endpoints[endpoint]["response"] = report["response"]
                    if len(endpoints[endpoint]["reports"]) <= 10:
                        endpoints[endpoint]["reports"].append(report)
                    else:
                        endpoints[endpoint]["reports"].pop(0)
                        endpoints[endpoint]["reports"].append(report)
                else:
                    pass
            write_json(jfile, file)
            return "routine_check_complete"
        else:
            return "check_format"


# Check Bulk Endpoints - /<mail>/check-all/
# <mail> - Admin Email
# Payload : {
#              password: <admin-password>
#           }

@app.route("/<mail>/check-all/", methods=["GET", "POST"])
def bulk_check(mail):
    bulk_check_config = request.get_json(force=True)
    password = bulk_check_config['password']
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
                report = format_report(check_result)
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


# Generate Report - /<mail>/generate/report/<type>
# <mail> - Admin Email
# <type> - cumulative / on-request / each-owner
# Payload : {
#              password: <admin-password>
#              endpoint: <url>
#           }

@app.route("/<mail>/generate/report/<type>", methods=["GET", "POST"])
def generate_reports(mail, type="cumulative"):
    report_config = request.get_json(force=True)
    password = report_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            if type == "cumulative":
                report = generate_cumulative_report(report_config_flag="all")
                content = {
                    "subject": "isRunning | Report",
                    "report_type": type,
                    "ep": "All Endpoints"
                }
                ret_val = mail_report(
                    attachment=report, recipient=user_cred['email'], content=content)
                if os.path.exists("./reports/"+report):
                    os.remove("./reports/"+report)
                else:
                    pass
                return ret_val
            elif type == "on-request":
                report = generate_cumulative_report(
                    report_config_flag=report_config['endpoint'])
                content = {
                    "subject": "isRunning | Report",
                    "report_type": "Summary",
                    "ep": report_config['endpoint']
                }
                ret_value = ""
                for mail_id in endpoints[report_config['endpoint']]['mail-list']:
                    ret_value = mail_report(
                        attachment=report, recipient=mail_id, content=content)
                if os.path.exists("./reports/"+report):
                    os.remove("./reports/"+report)
                else:
                    pass
                return ret_value
            elif type == "each-owner":
                ret_value = ""
                for endpoint in endpoints.keys():
                    report = generate_cumulative_report(
                        report_config_flag=endpoint)
                    content = {
                        "subject": "isRunning | Report",
                        "report_type": "Summary",
                        "ep": endpoint
                    }
                    for mail_id in endpoints[endpoint]['mail-list']:
                        ret_value = mail_report(
                            attachment=report, recipient=mail_id, content=content)
                    if os.path.exists("./reports/"+report):
                        os.remove("./reports/"+report)
                    else:
                        pass
                report = generate_cumulative_report(report_config_flag="all")
                content = {
                    "subject": "isRunning | Report",
                    "report_type": type,
                    "ep": "All Endpoints"
                }
                ret_value = mail_report(
                    attachment=report, recipient=user_cred['email'], content=content)
                if os.path.exists("./reports/"+report):
                    os.remove("./reports/"+report)
                else:
                    pass
                return ret_value
        else:
            return "credential_error"


# API Endpoint to Get Current Status of EPs - for FrontEnd Use Only
# <mail> - Admin Email
# Payload : {
#              password: <admin-password>
#           }


@app.route("/<mail>/get/status", methods=["GET"])
def get_status(mail):
    status_config = request.get_json(force=True)
    password = status_config['password']
    complete_string = mail+"#"+password
    with open('list.json') as f:
        jfile = json.load(f)
        user_cred = jfile['user']
        endpoints = jfile['endpoints']
        cred_hash = hashlib.sha1(complete_string.encode()).hexdigest()
        if user_cred['token'] == cred_hash:
            return endpoints
        else:
            return "credential_error"

# External Check - /check-uptime?endpoint=<url>
# No Payload


@app.route("/check-uptime", methods=["GET"])
def get_endpoint():
    endpoint = request.args.get('endpoint')
    return str(check_endpoint(endpoint))


if __name__ == '__main__':
    app.run(debug=True)
