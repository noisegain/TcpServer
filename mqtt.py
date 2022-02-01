import asyncio
from dataclasses import dataclass, field
from time import time, sleep

from paho.mqtt import client as mqtt_client


@dataclass(frozen=True)
class Controller:
    id: str
    date: float = field(default=time(), hash=False)

    def update(self):
        object.__setattr__(self, "date", time())

    def is_valid(self):
        return time() - self.date < 60


class MqttClient:
    BROKER = '192.168.1.2'
    PORT = 1883
    CLIENT_ID = 'python-server'
    USERNAME = "giv"
    PASSWORD = "999"
    controllers: list[Controller]

    def __init__(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self.client = client = mqtt_client.Client(self.CLIENT_ID)
        client.username_pw_set(self.USERNAME, self.PASSWORD)
        client.on_connect = on_connect
        client.connect(self.BROKER, self.PORT)
        print("Connecting")
        self.controllers = list()

    def subscribe(self, topic: str, listeners, loop):

        async def on_receive(msg):
            """Обработка пришедшего сообщения"""
            id = msg.topic.split('/')[0]
            if id in listeners:  # Если id прослушивается
                print(listeners[id])
                # Создание задачи на пересылку сообщения андройд клиенту
                asyncio.get_event_loop().create_task(
                    send_to_client(listeners[id], msg.payload + bytes("\n", "utf8"), loop))

            # Обновление даты последнего сообщения от контроллера
            for controller in self.controllers:
                if controller.id == id:
                    controller.update()
                    break
            else:
                self.controllers.append(Controller(id))
            print(self.controllers)

        def on_message(client, userdata, msg):
            """Callback ф-ия на приём сообщения"""
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            asyncio.run(on_receive(msg))  # Запуск новой задачи, для обработки пришедшего сообщения

        print("subscribing")
        client = self.client
        client.subscribe(topic)
        client.on_message = on_message
        client.loop_forever()

    def publish(self, message: str, topic: str):
        """Публикация сообщения"""
        client = self.client
        result = client.publish(topic, message)
        status = result[0]
        if status == 0:
            print(f"Send `{message}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

    def is_active(self, id):
        """Проверяет активен ли контроллер"""
        for controller in self.controllers:
            if controller.id == id:
                return True
        return False

    def validate(self):
        """Удаляет контроллеры, если они неактивны более минуты"""
        while True:
            print("Validating")
            self.controllers = [x for x in self.controllers if x.is_valid()]
            print(self.controllers)
            sleep(60)


async def send_to_client(clients, message, loop):
    print(f"Sending to: {len(clients)} clients")
    to_del = []
    for i, client in enumerate(clients):
        try:
            await loop.sock_sendall(client, message)
        except ConnectionAbortedError:
            to_del.append(i)
    for i in reversed(to_del):
        clients.pop(i)
