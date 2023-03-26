import os
import shutil
import threading
import psutil
import requests
import json
from flask import Flask, render_template, request , redirect
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    # Get the folder path from the request
    folder_path = request.form['folder_path']

    # Scan the folder and calculate disk usage
    disk_usage = get_disk_usage(folder_path)

    # Render the results template with the disk usage information
    return render_template('results.html', disk_usage=disk_usage)

@app.route('/delete', methods=['POST'])
def delete():
    # Get the file or folder path from the request
    path = request.form['path']

    # Delete the file or folder
    delete_file_or_folder(path)

    # Redirect back to the index page
    return redirect('/')

def get_disk_usage(path , op_file = None):
    # Get the total disk space and free disk space
    total, used, free = shutil.disk_usage(path)

    # Recursively scan the folder tree and calculate the size of each folder
    folder_sizes = {}
    for dirpath, dirnames, filenames in os.walk(path):
        folder_size = 0
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                folder_size += os.path.getsize(fp)
            except OSError:
                # Handle any permission errors or other issues
                pass
        folder_sizes[dirpath] = folder_size

    # Calculate the percentage of disk usage for each folder
    disk_usage = {}
    for folder_path, folder_size in folder_sizes.items():
        folder_usage = folder_size / total * 100
        disk_usage[folder_path] = folder_usage
        
    if op_file:
        with open(op_file, 'w') as f:
            json.dump(disk_usage, f)

    return disk_usage



def delete_file_or_folder(path):
    if os.path.isfile(path):
        # Delete the file
        os.remove(path)
    elif os.path.isdir(path):
        # Delete the folder and all its contents
        shutil.rmtree(path)

def monitor_disk_space():
    # Set the disk space threshold for the notification to 90%
    threshold = 90

    while True:
        # Get the current disk usage
        total, used, free = shutil.disk_usage('/')

        # Calculate the percentage of disk usage
        disk_usage = used / total * 100

        if disk_usage > threshold:
            # Send a notification to the Cockpit API endpoint
            data = {'message': 'Low disk space: {:.2f}% used'.format(disk_usage)}
            headers = {'Content-Type': 'application/json'}
            response = requests.post('http://localhost:9090/api/notifications', data=json.dumps(data), headers=headers)

        # Wait for 5 minutes before checking again
        time.sleep(300)

if __name__ == '__main__':
    # Start monitoring the disk space in a separate thread
    threading.Thread(target=monitor_disk_space).start()

    # Start the Flask web server
    app.run(debug=True)
