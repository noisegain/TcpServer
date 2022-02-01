import socket
import threading
from collections import defaultdict

from common import *
from mqtt import *

sessions = {}
listeners = defaultdict(list)
controllers = set()

data, user_logins = load_data()

mqtt = MqttClient()


def to_send(s):
    return bytes(s + '\n', "utf8")


async def handle_client(client):
    loop = asyncio.get_event_loop()
    await loop.sock_sendall(client, to_send("qawsedrftg"))
    while True:
        cmd, *request = (await loop.sock_recv(client, 255)).decode('utf8').split("&&")
        response = "Success"
        match cmd:
            case "login":
                login, password = request
                if login in user_logins and password == user_logins[login].password:
                    user: User = user_logins[login]
                    sessions[client] = user
                    listeners[user.id].append(client)
                else:
                    response = "Wrong login or password"
            case "cmd" if client in sessions:
                pass
            case "":
                return
            case _:
                response = "Unknown cmd"
        await loop.sock_sendall(client, to_send(response))


async def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("192.168.1.124", 8686))
    server.listen(8)
    server.setblocking(False)

    loop = asyncio.get_event_loop()

    threading.Thread(target=mqtt.subscribe, args=("#", listeners, loop)).start()
    threading.Thread(target=mqtt.validate).start()

    while True:
        client, _ = await loop.sock_accept(server)
        loop.create_task(handle_client(client))


asyncio.run(run_server())
