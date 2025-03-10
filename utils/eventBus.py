class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, topic: str, callback: callable, is_final: bool = False):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append({"callback": callback, "is_final": is_final})
    
    def publish(self, topic: str, data: dict):
        if topic in self.subscribers:
            stage_b = []
            for item in self.subscribers[topic]:
                stage_b.append(item) if item["is_final"] else item["callback"](data)
            for item in stage_b: item["callback"](data)