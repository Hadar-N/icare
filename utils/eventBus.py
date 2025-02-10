class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, topic: str, callback):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
    
    def publish(self, topic: str, data: dict):
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                callback(data)
