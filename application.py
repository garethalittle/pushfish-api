#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals
from flask import Flask, redirect, send_from_directory, request
import logging
from sqlalchemy.exc import OperationalError
import sys

from config import Config

_LOGGER = logging.getLogger(name="pushfish_API")

_LOGGER.info("creating Config object")
cfg = Config(create=True)

import database

from shared import db
from controllers import subscription, message, service, gcm, mqtt
from utils import Error

gcm_enabled = True
if cfg.google_api_key == '':
    _LOGGER.warning("WARNING: GCM disabled, please enter the google api key for gcm")
    gcm_enabled = False
if cfg.google_gcm_sender_id == 0:
    _LOGGER.warning('WARNING: GCM disabled, invalid sender id found')
    gcm_enabled = False

mqtt_enabled = True
if cfg.mqtt_broker_address == '':
    _LOGGER.warning("WARNING: MQTT disabled, please enter the address for mqtt broker")
    mqtt_enabled = False
if cfg.mqtt_broker_address == 0:
    _LOGGER.warning('WARNING: MQTT disabled, invalid address for mqtt broker')
    mqtt_enabled = False

app = Flask(__name__)
app.debug = cfg.debug
app.config['SQLALCHEMY_DATABASE_URI'] = cfg.database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
db.app = app

try:
    with app.app_context():
        database.init_db()
except Exception as err:
    _LOGGER.error("couldn't initialize database with URI: %s", cfg.database_uri)
    if cfg.GLOBAL_BACKTRACE_ENABLE:
        raise err
    else:
        sys.exit(1)


@app.route('/')
def index():
    return redirect('https://www.push.fish')


@app.route('/robots.txt')
@app.route('/favicon.ico')
def robots_txt():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/version')
def version():
    with open('.git/refs/heads/master', 'r') as f:
        return f.read(7)


@app.errorhandler(429)
def limit_rate(e):
    return Error.RATE_TOOFAST


app.register_blueprint(subscription)
app.register_blueprint(message)
app.register_blueprint(service)
if gcm_enabled:
    app.register_blueprint(gcm)
if mqtt_enabled:
    app.register_blueprint(mqtt)

if __name__ == '__main__':
    app.run()
