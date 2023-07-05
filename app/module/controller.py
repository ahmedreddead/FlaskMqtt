import json
import time

from flask import render_template, request, jsonify
from app import app,socketio

from flask_mqtt import Mqtt
from app.module import database
from flask import session

from flask import redirect, url_for
from datetime import timedelta


app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Set session duration (e.g., 7 days)
mqtt = Mqtt(app)
sensor_data = {}
sensor_types = ['temperature', 'humidity', 'motion_sensor', 'door_sensor', 'glass_break' ,'switch', 'siren']
sensor_counts = {}
is_first_load = True
page_loaded = False
#item_locations = [1,2,2,3]  # Default locations

host = '10.20.0.183'


@app.route('/process_locations', methods=['POST'])
def process_locations():
    item_locations = request.get_json()
    dashboard_id = session['dashboard_id']
    user_id = session.get('user_id')
    # Process the item locations as needed
    # Here, we simply print the item locations and return them as JSON response
    print(item_locations)
    session['item_locations'] = item_locations

    print(type(item_locations))
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    object.insert_positions_into_dashboard(item_locations,dashboard_id,user_id)
    object.disconnect()
    return jsonify(item_locations)

@app.route('/add-item', methods=['POST'])
def add_item():
    global sensor_counts
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    user_id = session.get('user_id')
    dashboard_id = 0
    sensor_data = request.json
    cursor = object.connection.cursor()
    Error_Flag = False
    #{'type': 'motion_sensor', 'id': '98553', 'protocol': 'wifi'}
    print(sensor_data)
    typeOfSensor = 'sensors'
    # Perform the necessary actions to add the sensor to the database
    if sensor_data['type'] in ["switch","siren"] :
        typeOfSensor = "actuators"

    # Execute the SQL query to retrieve the ID of the first dashboard
    cursor.execute("SELECT id FROM dashboards WHERE user_id = %s LIMIT 1", (user_id,))
    result = cursor.fetchone()
    print(result)
    if result is not None:
        dashboard_id = result[0]
    else:
        print("No dashboard found for user ID:", user_id)
        object.connection.close()
        exit()

    print(type (dashboard_id))
    print(type (sensor_data['id']))

    if typeOfSensor == "sensors" :
    # insert data base sensor
        if not object.check_sensorid(sensor_data['id']) :
            if object.insert_new_sensor(sensor_data['id'],sensor_data['protocol'],sensor_data['type']) :
                Error_Flag = True
    # insert dashboard new sensor
        if object.insert_sensor_to_dashboard(dashboard_id,sensor_data['id']) :
            Error_Flag = True

    if typeOfSensor == "actuators" :
    # insert data base actuators
        if not object.check_actuatorid(sensor_data['id']):
            if object.insert_new_actuator(sensor_data['id'], sensor_data['protocol'], sensor_data['type']) :
                Error_Flag = True
    # insert dashboard actuators
        if object.insert_actuators_to_dashboard(dashboard_id, sensor_data['id']) :
            Error_Flag = True




    # Return a JSON response

    print(sensor_data['type'],sensor_data['id'])
    #print(session["sensor_counts"])

    object.disconnect()


    if Error_Flag == False :
        response = {'message': 'item added successfully'}

        sensor_counts = session["sensor_counts"]
        if sensor_data['type'] not in sensor_counts.keys():
            sensor_counts[sensor_data['type']] = []
        if int(sensor_data['id']) not in sensor_counts[sensor_data['type']] :
            sensor_counts[sensor_data['type']].append(int(sensor_data['id']))

        session['sensor_counts'] = sensor_counts

        return jsonify(response), 200
    else:
        response = {'message': 'item Failed to add '}
        return jsonify(response), 404

@app.before_request
def check_first_load():
    pass

def get_data_database ():
    global  sensor_counts
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    sensor_counts = {key: [] for key in sensor_types}

    cursor = object.connection.cursor()
    check_query = "SELECT * FROM sensors"
    cursor.execute(check_query)
    result = cursor.fetchall()
    for row in result:
        if row[2] in sensor_types:
            sensor_counts[row[2]].append(row[0])
    check_query = "SELECT * FROM actuators"
    cursor.execute(check_query)
    result = cursor.fetchall()
    for row in result:
        if row[2] in sensor_types:
            sensor_counts[row[2]].append(row[0])
    cursor.close()
    object.connection.close()
    sensor_counts = {key: value for key, value in sensor_counts.items() if value}

    return sensor_counts

def get_data_From_dashboard():
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    user_id = session.get('user_id') # Assuming user ID is 1, replace with the actual user ID retrieval logic
    sensor_counts = {key: [] for key in sensor_types}
    # Query to retrieve sensor and actuator data from the first dashboard
    result = object.get_sensors_by_user(user_id)
    # Format the results as a list of dictionaries
    data = [{'id': row[0], 'name': row[1]} for row in result]
    for row in data:
        sensor_counts[row['name']].append(row['id'])
    sensor_counts = {key: value for key, value in sensor_counts.items() if value}
    print(sensor_counts)
    session["sensor_counts"] = sensor_counts
    return sensor_counts

def validate_credentials(username, password):
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()

    cursor = object.connection.cursor()
    check_query = "SELECT id FROM users WHERE name = %s AND password = %s"
    cursor.execute(check_query, (username, password))
    result = cursor.fetchone()
    user_id = result[0] if result else None
    cursor.close()
    object.connection.close()

    return user_id

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate the username and password against the database
        # Check if the credentials are correct and exist in the database
        user_id = validate_credentials(username, password)
        if user_id:
            # Save the username in the session
            session['username'] = username
            session['user_id'] = user_id
            session['dashboard_id'] = 1
            session.permanent = True  # Enable permanent session
            return redirect(url_for('dashboard'))
        else:
            error_message = "Invalid username or password"
    else:
        error_message = ""

    return render_template('login.html', error=error_message)

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))

@socketio.on('connect')
def handle_connect():
    # Access session in the WebSocket connection
    if 'first_load' not in session:  # Check if it's the first client connection
        session['first_load'] = False

def check_session_parameters() :
    # Access session in the WebSocket connection
    if 'user_id' not in session :
        return redirect(url_for('login'))
    if 'dashboard_id' not in session :
        return redirect(url_for('login'))
    if 'first_load' not in session:  # Check if it's the first client connection
        session['first_load'] = False
    if 'item_locations' not in session :
        session['item_locations'] = get_items_locations()
    if 'count' not in session :
        session['count'] = len(get_items_locations())


def get_items_locations () :
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    result = object.get_positions(session.get('user_id'),session.get('dashboard_id'))
    object.disconnect()
    return result

@app.route('/')
def index():
    sensor_types = ['temperature', 'humidity', 'switch' , 'siren' , 'motion_sensor' , 'door_sensor' , 'glass_break' ]
    return render_template('index.html',  sensor_types=sensor_types)

@app.route('/data')
def data():
    return jsonify(sensor_data)

@app.route('/user')
def user():
    global page_loaded
    """
    sensor_counts = {
        'door_sensor': [1, 2],
        'motion_sensor': [1, 2] ,
        'switch' : [33] ,
        'siren' : [55 ]
        # add more sensor types and IDs here
    }"""
    global is_first_load, sensor_counts
    first_load = session.get('first_load')
    sensor_counts = session.get('sensor_counts',False)
    print(sensor_counts)

    if is_first_load:
        # Perform the initialization tasks here
        sensor_counts = get_data_From_dashboard()
        for sensor_type in list(sensor_counts.keys()):
            for sensor_id in sensor_counts.get(sensor_type, []):
                #topic = f"micropolis/{sensor_type}/{sensor_id}"
                #mqtt.publish(topic, "unknown")
                #time.sleep(0.1)
                pass

        # Update the flag to indicate that the initialization has been done
        is_first_load = False
    """
    first_load = session.get('first_load')
    if not session or not first_load :
        session['first_load'] = True
        sensor_counts = get_data_database()
        # Publish initial "unknown" status for each sensor and actuator
        for sensor_type in list (sensor_counts.keys()):
            for sensor_id in sensor_counts.get(sensor_type, []):
                topic = f"micropolis/{sensor_type}/{sensor_id}"
                mqtt.publish(topic, "unknown")
    """
    if 'username' in session:
        # User is already logged in, render the user page
        return render_template('user.html', username=session['username'], sensor_counts=sensor_counts,page_loaded=page_loaded)
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    check_session_parameters()
    if 'username' not in session:
        return redirect(url_for('login'))

    '''
    count = 0
    sensor_counts = session.get('sensor_counts', False)
    items = session.get('item_locations', False)

    if not items :
        items = get_items_locations()
        print(items)

        items = []
        for x in sensor_counts.keys():
            for n in sensor_counts[x]:
                items.append({'itemId': n , 'partitionId': 'partition-'+str(count) , 'type' : str(x) })
        
    if sensor_counts :
        for x in sensor_counts.keys():
            for n in sensor_counts[x]:
                count += 1
    '''
    count = session.get('count')
    partition_width  = 200
    partition_height = 200
    padding = 60
    numPerRow = 5
    numItems = count // 4
    if type(count / 2) == float :
        numItems+= 1
    len_items = count  # Replace with the actual number of items
    #print(items)
    #print(sensor_counts)
    #session['item_locations']= items
    #print(session['item_locations'])


    if 'username' in session:
        # User is already logged in, render the user page
        return render_template('dashboard.html',item_locations=session['item_locations'],len_items=len_items, num_items=numItems, items_flask=session['item_locations'], username=session['username'], partition_width=partition_width,partition_height=partition_height,padding=padding , num_per_row =numPerRow )
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('#')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    #print(data)
    topic_parts = data['topic'].split('/')
    sensor_type = topic_parts[1]
    sensor_id = topic_parts[2]
    if sensor_type not in sensor_data:
        sensor_data[sensor_type] = {}
    sensor_data[sensor_type][sensor_id] = data['payload']
    socketio.emit(f'{sensor_type}_data', json.dumps(sensor_data[sensor_type]))

@socketio.on('actuator_command')
def handle_actuator_command(data):
    actuator_type = data['type']
    actuator_id = data['id']
    actuator_value = data['value']
    mqtt.publish(f'micropolis/{actuator_type}/{actuator_id}', actuator_value)