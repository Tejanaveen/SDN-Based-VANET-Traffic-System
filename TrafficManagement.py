import time                                                                                                                           
import random
import matplotlib.pyplot as plt
import numpy as np
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mn_wifi.cli import CLI
from mininet.log import setLogLevel, info
from shapely.geometry import Polygon, Point

poly = Polygon([(37.75850848099701, -122.50833008408812), (37.75911919711413, -122.49648544907835),(37.751620611284935, -122.4937388670471),(37.74863453749236, -122.50742886185911)])

class Vehicle:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.location = None
        self.accelerometer = random.randint(0, 100)
        self.gyroscope = random.randint(0, 100)
        self.emergency = False
        self.weather_condition = random.choice(["Clear", "Rain", "Snow", "Fog"])

    def update_location(self):
        min_x, min_y, max_x, max_y = poly.bounds
        while True:
            random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            if random_point.within(poly):
                self.location = random_point
                break

    def detect_accident(self):
        if self.accelerometer > 80 or self.gyroscope > 80:
            self.emergency = True

class TrafficManagementSystem:
    def __init__(self):
        self.vehicles = {}

    def add_vehicle(self, vehicle):
        self.vehicles[vehicle.vehicle_id] = vehicle

    def remove_vehicle(self, vehicle_id):
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]

    def send_alert(self, vehicle_id):
        if vehicle_id in self.vehicles and self.vehicles[vehicle_id].emergency:
            print(f"Sending alert to emergency services for vehicle {vehicle_id} at location {self.vehicles[vehicle_id].location}")
            self.vehicles[vehicle_id].emergency = False

def create_mininet_topology(tms):
    net = Mininet(controller=Controller, autoSetMacs=True)
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')

    info('*** Adding hosts\n')
    for vehicle_id, vehicle in tms.vehicles.items():
        h = net.addHost(f'h{vehicle_id}', ip=f'10.0.0.{vehicle_id}')
        net.addLink(h, s1)

    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])

    vehicle_locations = []
    emergency_locations = []
    emergency_counts = []
    accident_counts = []
    gyrometer_readings = []
    accelerometer_readings = []

    # Simulate vehicles moving and detecting accidents
    for _ in range(10):
        for vehicle_id in tms.vehicles.keys():
            vehicle = tms.vehicles[vehicle_id]
            vehicle.update_location()
            vehicle.detect_accident()
            if vehicle.emergency:
                tms.send_alert(vehicle_id)
                emergency_locations.append(vehicle.location)
        vehicle_locations.extend([vehicle.location for vehicle in tms.vehicles.values()])
        emergency_counts.append(sum([1 for vehicle in tms.vehicles.values() if vehicle.emergency]))
        accident_counts.append([sum([1 for vehicle in tms.vehicles.values() if vehicle.emergency and vehicle.gyroscope > 80]),
                                sum([1 for vehicle in tms.vehicles.values() if vehicle.emergency and vehicle.accelerometer > 80])])
        time.sleep(1)

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

    # Visualize the data

    # Extract latitudes and longitudes for plotting
    vehicle_latitudes = [location.y for location in vehicle_locations]
    vehicle_longitudes = [location.x for location in vehicle_locations]

    emergency_latitudes = [location.y for location in emergency_locations]
    emergency_longitudes = [location.x for location in emergency_locations]

    # Plot vehicle locations
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.scatter(vehicle_longitudes, vehicle_latitudes, color='blue', label='Vehicle Locations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Vehicle Locations')
    plt.legend()
    plt.grid(True)

    # Plot emergency locations
    plt.subplot(1, 2, 2)
    plt.scatter(emergency_longitudes, emergency_latitudes, color='red', label='Emergency Vehicle Locations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Emergency Vehicle Locations')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # Plot gyrometer and accelerometer readings over time
    plt.figure(figsize=(12, 6))

    # Original sensor data
    accel_original = []
    gyro_original = []

    for vehicle_id, vehicle in tms.vehicles.items():
        accel_original.append([vehicle.accelerometer] * 10)
        gyro_original.append([vehicle.gyroscope] * 10)

    # Generating replica sensor data with noise
    noise_factor = 0.2  # Adjust noise factor as needed
    accel_replica = [[value + np.random.uniform(-noise_factor * value, noise_factor * value) for value in values] for values in accel_original]
    gyro_replica = [[value + np.random.uniform(-noise_factor * value, noise_factor * value) for value in values] for values in gyro_original]

    # Plot gyrometer readings
    plt.subplot(2, 1, 1)
    for i in range(len(tms.vehicles)):
        plt.plot(range(10), gyro_replica[i], '--', label=f"Vehicle {i+1} Gyroscope")
    plt.xlabel("Time")
    plt.ylabel("Gyroscope Reading")
    plt.legend()

    # Plot accelerometer readings
    plt.subplot(2, 1, 2)
    for i in range(len(tms.vehicles)):
        plt.plot(range(10), accel_replica[i], '--', label=f"Vehicle {i+1} Accelerometer")
    plt.xlabel("Time")
    plt.ylabel("Accelerometer Reading")
    plt.legend()

    plt.tight_layout()
    plt.show()

# Create a traffic management system
tms = TrafficManagementSystem()

# Create and add vehicles to the system
for i in range(1, 6):
    vehicle = Vehicle(i)
    tms.add_vehicle(vehicle)

# Create and run the Mininet topology
create_mininet_topology(tms)
