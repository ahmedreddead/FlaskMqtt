import json
import time

from flask import render_template, request, jsonify
from app import app,socketio

from flask_mqtt import Mqtt
from app.module import database
from flask import session

from flask import redirect, url_for
from datetime import timedelta
host = '10.20.0.183'

def get_items_locations () :
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    result = object.get_positions(1,1)
    object.disconnect()
    return result


print(get_items_locations())