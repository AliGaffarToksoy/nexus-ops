import json
import time
import random
import logging
from faker import Faker
from kafka import KafkaProducer
from datetime import datetime

# Faker kütüphanesi ile sahte ama gerçekçi veriler üreteceğiz
fake = Faker()

# Kafka Producer Ayarları (localhost üzerinden bağlanıyoruz)
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'system-logs'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_producer():
    """Kafka'ya bağlanana kadar dener"""
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logging.info(f"Kafka'ya bağlandı: {KAFKA_BROKER}")
            return producer
        except Exception as e:
            logging.warning(f"Kafka bekleniyor... Hata: {e}")
            time.sleep(5)


def generate_log():
    """Gerçekçi kurumsal loglar üretir"""
    log_levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR", "CRITICAL"]
    services = ["payment-api", "auth-service", "frontend-web", "inventory-db"]

    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": random.choice(log_levels),
        "service": random.choice(services),
        "ip_address": fake.ipv4(),
        "user_agent": fake.user_agent(),
        "message": fake.sentence(nb_words=6)
    }
    return log_data


if __name__ == "__main__":
    logging.info("Log Generator başlatılıyor...")
    producer = get_producer()

    try:
        while True:
            log_entry = generate_log()
            # Logu Kafka kuyruğuna fırlat
            producer.send(TOPIC_NAME, log_entry)
            logging.info(f"Log Gönderildi: [{log_entry['level']}] {log_entry['service']}")

            # Saniyede 1-3 log atacak şekilde rastgele bekle
            time.sleep(random.uniform(0.3, 1.0))
    except KeyboardInterrupt:
        logging.info("Log Generator durduruldu.")
    finally:
        producer.close()