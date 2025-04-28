from mqtt_shared import Topics
from .data_singleton import DataSingleton

class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.__global_data = DataSingleton()
    
    def subscribe(self, topic: str, callback: callable, is_final: bool = False):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append({"callback": callback, "is_final": is_final})

    def __execute_callback(self, callback:callable, data:dict) -> dict:
        res = None
        try:
            res = callback(data)
        except Exception as e:
            self.__global_data.logger.error(e)
        return res
        
    
    def publish(self, topic: str, data: dict):
        if Topics.is_word_select(topic): topic = Topics.word_select()
        elif Topics.is_word_state(topic): topic = Topics.word_state()
        if topic in self.subscribers:
            stage_b = []
            for item in self.subscribers[topic]:
                stage_b.append(item) if item["is_final"] else self.__execute_callback(item["callback"],data)
            for item in stage_b: self.__execute_callback(item["callback"],data)