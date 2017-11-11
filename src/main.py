#!/bin/python3

import json
import docker
import docker_monitor
from flask import Flask, render_template, request, redirect, jsonify, url_for
from pymongo import MongoClient
from flask_apscheduler import APScheduler
import plotly.graph_objs as go
import plotly

app = Flask(__name__)
mongo_client = MongoClient('mongodb://mongo_user:mongo_pass@ds257485.mlab.com:57485/hackathon2017')
db = mongo_client.get_database()
collection = db['hackathon']

@app.route("/")
def index():
    record = collection.find().sort([('timestamp', -1)]).limit(1)[0]
    return render_template('index.html', record=record)

@app.route("/statistics")
def statistics():
    timestamp = []
    active_containers = []
    all_up = 0
    all_down = 0
    partial = 0
    for row in collection.find():
        count = 0
        for i in row['result']:
            if row['result'][i]['state'] != 'exited':
                count += 1
        timestamp.append(row['timestamp'])
        active_containers.append(count)
    for row in collection.find():
        row = [row['result'][i]['state'] for i in row['result']]
        if len(set(row)) == 1:
            if 'exited' in row:
                all_down += 1
            else:
                all_up +=1
        else:
            partial +=1
    data = [go.Scatter(x=timestamp, y=active_containers)]
    fig = go.Figure(data=data)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('statistics.html', graphJSON=graphJSON, all_up=all_up, all_down=all_down, partial=partial)


@app.route("/info/<containder_id>")
def get_info(containder_id):
    docker_client = docker.from_env()
    info = str(docker_client.containers.get(containder_id).attrs)
    return jsonify(json.loads(info.strip().replace("'", '"').replace('True', '"True"').replace('False', '"False"').replace('None', '"None"')))


@app.route("/refresh", methods=['POST'])
def refresh():
    docker_monitor.run()
    return redirect("/")

@app.route("/refresh_stat", methods=['POST'])
def refresh_stat():
    docker_monitor.run()
    return redirect("/statistics")

@app.route("/restart", methods=['POST'])
def restart():
    docker_client = docker.from_env()
    start_container_id = request.form.get("start")
    stop_container_id = request.form.get("stop")
    if start_container_id:
        docker_client.containers.get(start_container_id).start()
    if stop_container_id:
        docker_client.containers.get(stop_container_id).stop()
    docker_monitor.run()
    return redirect("/")

@app.route("/restart_all", methods=['POST'])
def restart_all():
    docker_client = docker.from_env()
    restart_container = request.form.get("restart")
    if restart_container:
        for id in docker_client.containers.list(all):
            docker_client.containers.get(id.short_id).restart()
    docker_monitor.run()
    return redirect("/")

if __name__ == '__main__':
    class Config(object):
        JOBS = [
            {
                'id': 'job1',
                'func': 'docker_monitor:run',
                'trigger': 'interval',
                'seconds': 300
            }
        ]
        SCHEDULER_API_ENABLED = True

    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    # Initial run when app starts
    docker_monitor.run()
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)