import flask
from flask_socketio import SocketIO

app = flask.Flask(__name__)
socketio = SocketIO(app)

from app.module.controller import *
from app.module.database import *



#from app.module.database import *