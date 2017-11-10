#!/bin/python3

import docker
from pymongo import MongoClient
from datetime import datetime

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
    return container_data

def insert_docker_data(client, table_name, data):
    db = client.get_database()
    collection = db[table_name]
    collection.insert_one(data)

def run():
    docker_client = docker.from_env()
    docker_data = get_docker_data(docker_client)
    # print(docker_data)
    mongo_client = MongoClient('mongodb://mongo_user:mongo_pass@ds257485.mlab.com:57485/hackathon2017')
    insert_docker_data(mongo_client, 'hackathon', docker_data)

# run()
