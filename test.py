import datetime
now = datetime.datetime.utcnow()
print(now.hour)

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
                        endpoints[endpoint]["reports"].pop(index=0)
                        endpoints[endpoint]["reports"].append(report)
                else:
                    pass
            write_json(jfile, file)
            return "routine_check_complete"
        else:
            return "check_format"