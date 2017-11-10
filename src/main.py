#!/bin/python3

from flask import Flask, render_template,request,redirect,url_for
from pymongo import MongoClient
from flask_apscheduler import APScheduler
import docker_monitor
import docker

app = Flask(__name__)
mongo_client = MongoClient('mongodb://mongo_user:mongo_pass@ds257485.mlab.com:57485/hackathon2017')
db = mongo_client.get_database()
collection = db['hackathon']

@app.route("/")
def index():
    record = collection.find().sort([('timestamp', -1)]).limit(1)[0]
    return render_template('index.html', record=record)

@app.route("/restart", methods=['POST'])
def stop():
    docker_client = docker.from_env()
    start_container_id = request.form.get("start")
    stop_container_id = request.form.get("stop")
    if start_container_id:
        docker_client.containers.get(start_container_id).start()
    if stop_container_id:
        docker_client.containers.get(stop_container_id).stop()
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

    app.run(debug=True)