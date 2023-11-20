from __future__ import annotations

import json

from prefect import flow, task
from clickhouse_connect import create_client
from clickhouse_connect.driver import Client

@task
def ping(client: Client):
    print(client.ping())

@task
def createTable(client: Client):
    client.command("""
    DROP TABLE IF EXISTS requests;
    create table requests
    (
        id UUID default generateUUIDv4(),
        url String,
        timestamp TIMESTAMP default now()
    ) engine = Memory;
    """)

@task
def seedTable(client: Client):
    client.command("""
    INSERT INTO requests(url) VALUES ('https://www.google.com'), ('https://www.fingerprint.com') 
    """)


def dumpData(data):
    file = open('./dump.json', 'a')
    file.write(json.dumps(data))
    file.close()

@task
def storeData(client: Client):
    query = client.query("SELECT url, toString(timestamp) FROM requests ORDER BY id ASC LIMIT 100")
    dumpData(query.result_set)


@flow(log_prints=True)
def clickhouse(host: str = "clickhouse", username: str = "default"):
    client = create_client(host=host, username=username)
    ping(client)
    createTable(client)
    seedTable(client)
    storeData(client)

if __name__ == "__main__":
    clickhouse.serve(name="Fetch Data")
