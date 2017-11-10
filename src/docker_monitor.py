#!/bin/python3

import docker
from pymongo import MongoClient
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def get_docker_data(client):
    container_data = {}
    container_data["result"] = {}
    index = 0
    for container in client.containers.list(all):
        index_str = str(index)
        container_data["result"][index_str] = {}
        container_data["result"][index_str]['id'] = container.short_id
        container_data["result"][index_str]['name'] = container.name
        container_data["result"][index_str]['status'] = container.status
        for container_ps in container.client.api.containers(all=True):
            if  container.id == container_ps['Id']:
                container_data["result"][index_str]['state'] = container_ps['State']
                container_data["result"][index_str]['status'] = container_ps['Status']
        index += 1
    container_data['timestamp'] = datetime.now()
    container_data['timestamp_sec'] = datetime.now().timestamp()
    return container_data

def maintain_docker_data(client, table_name, data):
    db = client.get_database()
    collection = db[table_name]
    collection.insert_one(data)
    old_timestamp = datetime.now().timestamp() - 18000
    collection.delete_many({'timestamp_sec': {'$lt': str(old_timestamp)}})

def send_mail(data):
    result = data['result']
    failed_containers = []

    for row in result:
        if result[row]['state'] != 'running':
            failed_containers.append(result[row]['name'])

    if failed_containers:
        body = "Application " + str(failed_containers) + " went down at " + str(data['timestamp']) + ". Please investigate. You can start the failed container[s] via http://127.0.0.1:5000/"
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("docker.server123@gmail.com", "kingking@")
        msg = MIMEMultipart()
        msg['From'] = 'docker.server123@gmail.com'
        msg['To'] = "yongzheng0809@gmail.com"
        msg['Subject'] = '[URGENT] Container down'
        msg.attach(MIMEText(body, 'plain'))
        server.sendmail("docker.server123@gmail.com", "yongzheng0809@gmail.com", msg.as_string())
        server.quit()

def run():
    docker_client = docker.from_env()
    docker_data = get_docker_data(docker_client)
    mongo_client = MongoClient('mongodb://mongo_user:mongo_pass@ds257485.mlab.com:57485/hackathon2017')
    maintain_docker_data(mongo_client, 'hackathon', docker_data)
    send_mail(docker_data)

# run()

