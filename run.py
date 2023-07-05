from app import app,socketio


#app.run(debug=True, host='127.0.0.1', port=2000)
socketio.run(app, debug=True, host='0.0.0.0', port=2000,allow_unsafe_werkzeug=True)