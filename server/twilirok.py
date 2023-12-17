#!/usr/bin/env python3
import json

from pyngrok import conf, ngrok
from twilio.rest import Client


def handle_log(log):
    print(str(log))


def load_config(file_name):
    f = open(file_name)
    _data = json.load(f)
    f.close()
    return _data


def start_ngrok(_data):
    conf.get_default().monitor_thread = False
    conf.get_default().log_event_callback = handle_log
    conf.get_default().auth_token = _data["ngrok"]["auth_token"]

    http_tunnel = ngrok.connect(_data["port"])
    ngrok_url = http_tunnel.public_url
    print(f"Ngrok URL: {ngrok_url}")

    return ngrok_url


def update_twiml_app(_data, _http_tunnel):
    updates = dict()
    print("\nUpdating TwiML App:")
    for key in _data["updates"]:
        if key[-4:] == "_url" or key[-9:] == "_callback":
            updates[key] = _http_tunnel + _data["updates"][key]
        else:
            updates[key] = _data["updates"][key]
        print(key + ': ' + updates[key])

    client = Client(_data["twilio"]["account_sid"], _data["twilio"]["auth_token"])
    client.applications(_data["twilio"]["twiml_app_sid"]).update(**updates)

    return client


def run():
    data = load_config("config.json")
    http_tunnel = start_ngrok(data)
    client = update_twiml_app(data, http_tunnel)
    ngrok_process = ngrok.get_ngrok_process()

    try:
        print("\nListening")
        ngrok_process.proc.wait()
    except KeyboardInterrupt:
        print("Stopping")
        ngrok.kill()


if __name__ == "__main__":
    run()
