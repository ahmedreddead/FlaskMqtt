import threading

from app import app,socketio,check_push_alerts


#app.run(debug=True, host='127.0.0.1', port=2000)



t = threading.Thread(target=check_push_alerts)
t.start()

socketio.run(app, debug=True, host='0.0.0.0', port=2000,allow_unsafe_werkzeug=True)