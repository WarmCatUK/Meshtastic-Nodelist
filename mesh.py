import time
import os
import sys
import math
from pubsub import pub
from meshtastic.tcp_interface import TCPInterface
from meshtastic import portnums_pb2
from datetime import datetime
from tabulate import tabulate

node_ip = '10.0.1.95'  # Your meshtastic node address

def clear_screen():
    # Clear the screen based on the operating system
    os.system('cls' if os.name == 'nt' else 'clear')
    
def get_node_info(node_ip):
    print("Tcp Interface initialising...")
    local = TCPInterface(hostname=node_ip)
    # it's possible to use serial connection using meshtastic.serial_interface.SerialInterface()
    # although I haven't tried that method.
    node_info = local.nodes
    local.close()
    print("Node info retrieved.")
    return node_info

def parse_node_info(node_info):
    print("Parsing node info...")
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown'),
                'longName': node.get('user', {}).get('longName', 'Unknown'),
                'role': node.get('user', {}).get('role', 'Client'),
                'hwModel': node.get('user', {}).get('hwModel', 'Unknown'),
                'latitude': node.get('position', {}).get('latitude', None),
                'longitude': node.get('position', {}).get('longitude', None)
            },
            'hopsAway': node.get('hopsAway', 'Direct/Unknown'),
            'lastHeard': node.get('lastHeard', 99999)
        })
    print("Node info parsed.")
    return nodes

def difference_with_current_time(unix_time):
    if unix_time == 0:
        return float('inf')
    now = int(time.time())
    return (now - unix_time) / 60

def convert_unix_time_to_local_readable(unix_time):
    if unix_time == 0:
        return "Never"
    return datetime.fromtimestamp(unix_time).astimezone().strftime('%Y-%m-%d %H:%M:%S')

def calculate_minutes_since_last_heard(unix_time):
    if unix_time == 99999:
        return "Never"
    now = datetime.now().astimezone()
    last_heard_time = datetime.fromtimestamp(unix_time).astimezone()
    minutes_difference = (now - last_heard_time).total_seconds() / 60
    return f"{int(minutes_difference)} min"

def haversine(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def main():

    # Your current location
    current_lat = 54.9818603  # Replace with your current latitude
    current_lon = -1.4193444  # Replace with your current longitude
    
    print(f"Using node IP: {node_ip}")

    while True:
        # Retrieve and parse node information
        node_info = get_node_info(node_ip)
        node_list = parse_node_info(node_info)

        # Filter nodes seen within the last 120 minutes
        filtered_node_list = [node for node in node_list if difference_with_current_time(node['lastHeard']) <= 120]

        # Sort node list by 'lastHeard' in descending order
        sorted_node_list = sorted(filtered_node_list, key=lambda x: x['lastHeard'], reverse=True)

        # Prepare data for tabulate
        table_data = []
        for node in sorted_node_list:
            readable_time = convert_unix_time_to_local_readable(node['lastHeard'])
            minutes_since_last_heard = calculate_minutes_since_last_heard(node['lastHeard'])
            distance = "N/A"
            if node['user']['latitude'] is not None and node['user']['longitude'] is not None:
                distance = f"{haversine(current_lat, current_lon, node['user']['latitude'], node['user']['longitude']):.2f} km"

            table_data.append([
                node['num'],
                node['user']['shortName'],
                node['user']['longName'],
                node['user']['role'],
                node['user']['hwModel'],
                node['hopsAway'],
                distance,
                readable_time,
                minutes_since_last_heard
            ])

        # Print node list in tabular format
        headers = ["Node ID", "Short Name", "Long Name", "Role", "HW Model", "Hops", "Distance", "Last Heard", "Ago"]
        colalign = ("left", "left", "left", "left", "left", "left", "left", "left", "right")
        table = tabulate(table_data, headers=headers, tablefmt="mixed_grid", colalign=colalign)
        
        # Clear the screen and print the updated table
        clear_screen()
        print(table)

        # Wait for 60 seconds before refreshing
        time.sleep(60)

if __name__ == "__main__":
    main()
