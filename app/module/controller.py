import json
import threading
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
sensor_types = [ 'temperature', 'humidity', 'motion_sensor', 'door_sensor', 'glass_break' ,'switch', 'siren' ]
sensor_counts = {}
is_first_load = True
page_loaded = False

host = '10.20.0.183'


def create_database_object () :
    object = database.Database(host, 3306, "grafana", "pwd123", "grafanadb")
    object.connect()
    return  object

@app.route('/process_locations', methods=['POST'])
def process_locations():
    item_locations = request.get_json()
    # Process the item locations as needed
    # Here, we simply print the item locations and return them as JSON response
    session['item_locations'] = item_locations
    object = create_database_object()
    update_process_location(item_locations,object)
    object.disconnect()

    return jsonify(item_locations)

def update_process_location (item_locations,object) :
    object.insert_positions_into_dashboard(item_locations,session['dashboard_id'],session.get('user_id'))

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

@app.route('/delete-item',methods =['POST'])
def delete_item () :
    item_data = request.json
    print(type(item_data))
    print(item_data)
    deleted_item_id , deleted_item_type = str (item_data['deletedItem']).split(',')
    object= create_database_object()

    if deleted_item_type == 'siren' or deleted_item_type == 'switch' :
        if deleted_item_type == 'switch' :
            deleted_item_type = ' relay_switch'
        status = object.delete_actuator(deleted_item_id,deleted_item_type)
    else:
        status = object.delete_sensor(deleted_item_id,deleted_item_type)

    if status :
        response = {'message': 'item not added '}
        return jsonify(response), 404
    else:
        response = {'message': 'item added '}
        return jsonify(response), 200

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

def get_data_From_dashboard(object):
    user_id = session.get('user_id') # Assuming user ID is 1, replace with the actual user ID retrieval logic
    sensor_counts = {key: [] for key in sensor_types}
    # Query to retrieve sensor and actuator data from the first dashboard
    result = object.get_sensors_by_user(user_id)
    # Format the results as a list of dictionaries
    data = [{'id': row[0], 'name': row[1]} for row in result]
    for row in data:
        if row['name'] != 'temp' :
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
    if 'first_load' not in session:  # Check if it's the first client connection
        session['first_load'] = False
    if 'user_id' not in session or 'dashboard_id' not in session:
        return redirect(url_for('login'))


    object = create_database_object()
    session['sensor_counts'] = get_data_From_dashboard(object)
    session['item_locations'] = get_items_locations(object)
    if not session['item_locations'] :
            counter = 0
            items = []
            for x in session['sensor_counts'].keys():
                for n in session['sensor_counts'][x]:
                    items.append({'itemId': n, 'partitionId': 'partition-' + str(counter), 'type': str(x)})
                    counter +=1
            session['item_locations'] = items
            update_process_location(session['item_locations'],object)

    session['count'] = len(session['item_locations'])


    max_partition = max(int(d['partitionId'].split('-')[1]) for d in session['item_locations'])
    sensor_counts = session['sensor_counts']
    item_locations = session['item_locations']
    list_of_ids = []
    list_of_typeids = []
    for dic in item_locations :
        list_of_ids.append(dic['itemId'])
        list_of_typeids.append(dic['type'])
    #and list_of_typeids[list_of_ids.index(id)] == type
    for type in sensor_counts.keys():
        for id in sensor_counts[type]:
            if id not in list_of_ids  :
                max_partition += 1
                session['item_locations'].append({'itemId': id, 'partitionId': 'partition-' + str(max_partition), 'type': str(type)})
                update_process_location(session['item_locations'],object)
                session['count'] +=1

    object.disconnect()

def get_items_locations (object) :
    result = object.get_positions(session.get('user_id'),session.get('dashboard_id'))
    result = sorted(result, key=lambda x: int(x['partitionId'].split('-')[1]))
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

    count = session.get('count')
    partition_width  = 200
    partition_height = 200

    padding = 50
    numPerRow = 4
    numItems = ( count // numPerRow )+ 1
    len_items = count  # Replace with the actual number of items

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


def do_action (action_id, object ) :
    actons = object.get_actions(action_id)
    list_of_actions = []
    for i in actons.keys() :
        for value in actons[i] :
            if i =='time' :
                sec , order = value
                list_of_actions.insert(order-1,(i , sec))
            else:
                id , status , order = value
                list_of_actions.insert(order-1 ,(i , id, status) )


    for tuple in list_of_actions :
        if tuple[0] == 'siren' or tuple[0] == 'switch' :
            data = { 'type' : tuple[0] , 'id' : tuple[1] , 'value' : tuple[2]}
            handle_actuator_command(data)
        else:
            time.sleep(int (tuple[1]) )

def do_action_thread(action_id):
    # Perform the necessary action
    do_action(action_id, create_database_object())
# Function to check for new rows periodically
def check_push_alerts():
    while True:
        try:
            object = create_database_object()
            rows = object.get_push_alert()
            if rows :
                for row in rows:
                    event_id, action_id = row
                    t = threading.Thread(target=do_action_thread, args=(action_id,))
                    t.start()
                    #do_action(action_id, object)
                    object.delete_push_alert(action_id)
            object.disconnect()

        except Exception as e:
            print("Error in push alerts:", e)
            object = create_database_object()



