import json
import logging
from kafka import KafkaConsumer
from opensearchpy import OpenSearch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] %(message)s')

KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'system-logs'
OPENSEARCH_HOST = 'localhost'
OPENSEARCH_PORT = 29092

# OpenSearch Bağlantısı (Lokal test için SSL ve şifreleme kapalı)
client = OpenSearch(
    hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)


def start_indexing():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest',  # Sadece yeni gelen logları al
        enable_auto_commit=True,
        group_id='nexus-indexer-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    logging.info(f"📡 Kafka dinleniyor ({TOPIC_NAME}) ve OpenSearch'e aktarılıyor...")

    try:
        for message in consumer:
            log_data = message.value

            # Veriyi OpenSearch'te 'nexus-logs' endeksine yaz
            response = client.index(
                index='nexus-logs',
                body=log_data
            )
            logging.info(f"💾 OpenSearch'e yazıldı | Servis: {log_data['service']} | Seviye: {log_data['level']}")
    except KeyboardInterrupt:
        logging.info("🛑 Indexer durduruldu.")
    finally:
        consumer.close()


if __name__ == '__main__':
    start_indexing()