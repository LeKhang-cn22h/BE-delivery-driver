class RabbitMQClient:
    def __init__(self):
        self.connection = None

    async def connect(self):
        print("RabbitMQ connected")

    async def consume(self):
        pass

    async def disconnect(self):
        print("RabbitMQ disconnected")
