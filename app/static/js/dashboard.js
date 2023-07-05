var a7a = "A7a";
console.log(a7a)
function getSensorIcon(sensorType, sensorStatus) {
    switch (sensorType) {
            
        case 'temperature':
            
            return '<i class="fa fa-thermometer-half sensor-icon"></i>';
            
        case 'humidity':
            return '<i class="fa fa-tint sensor-icon"></i>';
            
        case 'motion_sensor':
            if (sensorStatus === 'No Motion') {
                return '<img src="static/photo/motionno.png" class="sensor-icon"  width="140" height="140">';
            } else if (sensorStatus === 'Motion Detected') {
                return '<img src="static/photo/motiond.png" class="sensor-icon"  width="140" height="140">';
            }
            
        case 'door_sensor':
            if (sensorStatus === 'opened') {
                return '<img src="static/photo/door.png" class="sensor-icon"  width="140" height="140">';
            } else if (sensorStatus === 'closed') {
                return '<img src="static/photo/doorclosed.png" class="sensor-icon"  width="140" height="140">';
            }
            
        default:
            return '';
        }
}

function getActuatorIcon(actuatorType, actuatorValue) {
    let actuatorIconClass;
    if (actuatorValue === 'on') {
        actuatorIconClass = 'actuator-icon-on';
    } else {
        actuatorIconClass = 'actuator-icon-off';
    }
    switch (actuatorType) {
        case 'switch':
            return `<img src="static/photo/light${actuatorValue === 'on' ? 'on' : 'off'}.png" class="actuator-icon"  width="170" height="170">`;                // add more actuator types and icons here
        case 'siren':
            return `<img src="static/photo/siren${actuatorValue === 'on' ? 'on' : 'off'}.png" class="actuator-icon"  width="170" height="170">`;                // add more actuator types and icons here
        default:
            return '';
    }
}

function updateSensorData(sensorType, sensorData) {
    for (let sensorId in sensorData) {
        let sensorElementId = `${sensorType}${sensorId}`;
        let sensorElement = document.getElementById(sensorElementId);
        if (sensorElement) {
            let sensorValue = sensorData[sensorId];
            let lastUpdated = new Date().toLocaleTimeString();
            sensorElement.innerHTML = `
                <div class="sensor">
                    ${getSensorIcon(sensorType,sensorValue )}
                    <div class="sensor-name">${sensorType} ${sensorId}</div>
                    <div class="sensor-value">${sensorValue || 'Unknown'}</div>
                    <div class="last-updated">Last updated: ${lastUpdated}</div>
                </div>
            `;
        }
    }
}

function updateActuatorData(actuatorType, actuatorData) {
    for (let actuatorId in actuatorData) {
        let actuatorElementId = `${actuatorType}${actuatorId}`;
        let actuatorElement = document.getElementById(actuatorElementId);
        if (actuatorElement) {
            let actuatorValue = actuatorData[actuatorId];
            let lastUpdated = new Date().toLocaleTimeString();
            actuatorElement.innerHTML = `
                <div class="actuator">
                    ${getActuatorIcon(actuatorType, actuatorValue)}
                    <div class="actuator-name">${actuatorType} ${actuatorId}</div>
                    <div class="actuator-value">${actuatorValue || 'Unknown'}</div>
                    <div class="last-updated">Last updated: ${lastUpdated}</div>
                </div>
            `;
            actuatorElement.setAttribute('data-value', actuatorValue);
        }
    }
}

function toggleActuator(actuatorType, actuatorId) {
    let actuatorElementId = `${actuatorType}${actuatorId}`;
    let actuatorElement = document.getElementById(actuatorElementId);
    let actuatorValue = actuatorElement.getAttribute('data-value');
    let newActuatorValue = actuatorValue === 'on' ? 'off' : 'on';
    socket.emit('actuator_command', {
        type: actuatorType,
        id: actuatorId,
        value: newActuatorValue
    });
}

var socket = io.connect('http://' + document.domain + ':' + location.port);
var xhr = new XMLHttpRequest();
xhr.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var data = JSON.parse(this.responseText);
                for (let deviceType in data) {
                    if (deviceType == 'switch'  ) {
                        updateActuatorData(deviceType, data[deviceType]);
                    } else {
                        if (deviceType == 'siren'  ) {
                            updateActuatorData(deviceType, data[deviceType]);
                    }   else {
                            updateSensorData(deviceType, data[deviceType]);
                    }
                    }

                }
            }
        };
xhr.open('GET', '/data', true);
xhr.send();

var sensorCounts = {{ sensor_counts|tojson }};
for (let sensorType in sensorCounts) {
            let sensorIds = sensorCounts[sensorType];
            let sensorTypeElement = document.createElement('div');
            sensorTypeElement.id = sensorType;
            sensorTypeElement.className = 'sensor-type';
            document.getElementById('data').appendChild(sensorTypeElement);
            for (let i = 0; i < sensorIds.length; i++) {
                let sensorId = sensorIds[i];
                let deviceElement;
                if (sensorType == 'switch'|| sensorType == 'siren' ) {
                    deviceElement = document.createElement('a');
                    deviceElement.onclick = function () {
                        toggleActuator(sensorType, sensorId);
                    };
                    deviceElement.className = 'actuator btn btn-light';
                    deviceElement.innerHTML = `${getActuatorIcon(sensorType, 'off')}`;
                } else {
                    deviceElement = document.createElement('div');
                    deviceElement.className = 'sensor';
                    deviceElement.innerHTML = `${getSensorIcon(sensorType)}`;
                }
                deviceElement.id = `${sensorType}${sensorId}`;
                document.getElementById(sensorType).appendChild(deviceElement);
            }
            if (sensorType == 'switch' || sensorType == 'siren' ) {
                socket.on(`${sensorType}_data`, function (data) {
                    let actuatorData = JSON.parse(data);
                    updateActuatorData(sensorType, actuatorData);
                });

            } else {
                socket.on(`${sensorType}_data`, function (data) {
                    let sensorData = JSON.parse(data);
                    updateSensorData(sensorType, sensorData);
                });
            }
        }

     // Add an event listener to the "Add Item" button

function additem() {
  // Display the loading message
      document.getElementById("loading-div").style.display = "block";
      var successMessage = document.getElementById("success-message");

  
  // Simulate a delay (replace this with your actual request logic)
  
  // Get the values of the sensor attributes
        var type = document.getElementById('item-type').value;
        var id = document.getElementById('item-id').value;
        var protocol = document.getElementById('item-protocol').value;

  // Create a JSON object with the sensor data
        var sensorData = {
            type: type,
            id: id,
            protocol: protocol
        };

  // Send an AJAX POST request to the Flask API
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/add-item', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
      // Hide the loading message
      
      // Check the response status
            if (xhr.status === 200) {
        // Item added successfully
                document.getElementById("loading-div").style.display = "none";
                successMessage.style.display = "block";
                var response = JSON.parse(xhr.responseText);
                console.log(response);
                var addItemModal = document.getElementById('add-item-modal');
                setTimeout(function() {
                successMessage.style.display = "none";
                addItemModal.style.display = 'none';
                }, 3000);

        
                setTimeout(function() {
                location.reload();
                }, 5000);
          
            } else {
        // Item not added successfully
                document.getElementById("loading-div").style.display = "none";
                var errorMessage = document.getElementById("error-message");
                errorMessage.style.display = "block";

                console.log('Item not added successfully');
                var addItemModal = document.getElementById('add-item-modal');
                setTimeout(function() {
                errorMessage.style.display = "none";
                addItemModal.style.display = 'none';
                }, 5000);
        
            }
            }
        };
        xhr.send(JSON.stringify(sensorData));

        // Close the modal dialog after adding the item
        var addItemModal = document.getElementById('add-item-modal');
        addItemModal.style.display = 'block';
        }


  // Add an event listener to the "Add Item" button
var addItemButton = document.getElementById('add-item-button');
addItemButton.addEventListener('click', function () {
    var addItemModal = document.getElementById('add-item-modal');
    addItemModal.style.display = 'block';
  // Add an event listener to the close button in the modal dialog
    var closeBtn = document.getElementsByClassName('close')[0];
    
    closeBtn.addEventListener('click', function () {
        var addItemModal = document.getElementById('add-item-modal');
        addItemModal.style.display = 'none';
    });

});

  // Add an event listener to the "Add" button in the modal dialog
var addConfirmButton = document.getElementById('add-item-confirm');
addConfirmButton.addEventListener('click', additem);

let pageLoaded = {{ page_loaded|lower }};
if (!pageLoaded) {
    function performInitialUpdate() {
        for (let sensorType in sensorCounts) {
            if (sensorType == 'switch' || sensorType == 'siren') {
                let sensorIds = sensorCounts[sensorType];
            
                for (let i = 0; i < sensorIds.length; i++) {
                    let actuatorId = sensorIds[i];
                    let actuatorElementId = `${sensorType}${actuatorId}`;
                    let actuatorElement = document.getElementById(actuatorElementId);
                    if (actuatorElement) {
                        let actuatorValue ;
                        let lastUpdated = new Date().toLocaleTimeString();
                        actuatorElement.innerHTML = `
                        <div class="actuator">
                            ${getActuatorIcon(sensorType, actuatorValue)}
                            <div class="actuator-name">${sensorType} ${actuatorId}</div>
                            <div class="actuator-value">${actuatorValue || 'Unknown'}</div>
                            <div class="last-updated">Last updated: ${lastUpdated}</div>
                        </div>
                    `;
                        actuatorElement.setAttribute('data-value', actuatorValue);
                    }
                }
        
        
            } else {
                let sensorIds = sensorCounts[sensorType];
                for (let i = 0; i < sensorIds.length; i++) {
                    let sensorId = sensorIds[i];
                    let sensorElementId = `${sensorType}${sensorId}`;
                    let sensorElement = document.getElementById(sensorElementId);
                    if (sensorElement) {
                        let sensorValue;
                        let lastUpdated = new Date().toLocaleTimeString();
                        sensorElement.innerHTML = `
                            <div class="sensor">
                            ${getSensorIcon(sensorType, sensorValue)}
                            <div class="sensor-name">${sensorType} ${sensorId}</div>
                            <div class="sensor-value">${sensorValue || 'Unknown'}</div>
                            <div class="last-updated">Last updated: ${lastUpdated}</div>
                            </div>
                            `;
                    }
                }
            }
        }
        pageLoaded = true;
    }

    if (document.readyState === 'complete' || (document.readyState !== 'loading' && !document.documentElement.doScroll)) {
        performInitialUpdate();
    } else {
        document.addEventListener('DOMContentLoaded', performInitialUpdate);
    }}
        
