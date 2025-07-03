from confluent_kafka import Producer
from confluent_kafka import KafkaError
import json
import dotenv
import os
import time

class HeartDataProducer:
    def __init__(self, bootstrap_servers, topic):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})
        self.topic = topic

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"Delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send_heart_data(self, data, patient_id=None):
        """
        Sends heart data to the Kafka topic.

        Args:
            data (dict): The heart data to send.
        """
        try:
            value = json.dumps(data).encode('utf-8')
            self.producer.produce(self.topic, value=value, callback=self.delivery_report)
            self.producer.flush()
            print(f"Broker accept patient num {patient_id} correctly ✔️")
        except KafkaError as e:
            print(f"Failed to send message: {e}")

    def getpatient_data(self, datapath="./data/patiences.json", patient_id=1) -> dict:
        """
        Retrieves heart data for a specific patient.
        
        Returns:
            dict: The heart data for the patient.
        """
        with open("./data/patiences.json") as f:
            records = json.load(f)
            patient_current = {"idx": patient_id}
            idx = patient_current["idx"]
            record = records[idx]
            return record

# Example usage:
if __name__ == "__main__":
    dotenv.load_dotenv()
    bootstrap_servers = os.getenv('bootstrap_servers', "localhost:9091")
    topic = os.getenv('topic')  # This will be "patient" from .env
    
    print(f"Connecting to Kafka broker at {bootstrap_servers}, topic: {topic}")
  
    # FIX: Use the topic variable, not hardcoded "topic"
    producer = HeartDataProducer(bootstrap_servers=bootstrap_servers, topic=topic)
    patient_id = 0
    
    while True:
        try:
            sample_data = producer.getpatient_data("./data/patiences.json", patient_id=patient_id)
            print(f"Sending data: {sample_data}")               
            producer.send_heart_data(sample_data, patient_id)
            time.sleep(4)
            patient_id += 1
            print("waiting 4s ...")
        except Exception as e:
            print(f"Error: {e}")
            break