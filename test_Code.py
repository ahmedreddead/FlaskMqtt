import datetime
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


def do_action (action_id) :
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()

    actons = object.get_actions(action_id)
    list_of_actions = []
    print(list_of_actions)

    for i in actons.keys() :
        for value in actons[i] :
            if i =='time' :
                sec , order = value
                list_of_actions.insert(order-1,(i , sec))
            else:
                id , status , order = value
                list_of_actions.insert(order-1 ,(i , id, status) )


    print(actons)
    print(list_of_actions)



def get_items_locations () :
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    #object.insert_motion_sensor_reading(3321 , 'Motion Detected' ,datetime.datetime.now() )

    object.insert_door_sensor_reading(9988,'opened',datetime.datetime.now())
    object.disconnect()



print(do_action(66))