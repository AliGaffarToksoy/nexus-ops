import json
import uuid
import boto3
from kafka import KafkaConsumer
from opensearchpy import OpenSearch

# --- 1. KAFKA AYARLARI (DEDEKTİF MODU) ---
consumer = KafkaConsumer(
    bootstrap_servers=['127.0.0.1:29092'],
    auto_offset_reset='earliest',
    group_id=f"nexus-cloud-group-{uuid.uuid4()}"
)

# KAFKA'NIN RÖNTGENİNİ ÇEKİYORUZ:
aktif_topicler = consumer.topics()
print(f"🔍 Kafka'daki Mevcut Odalar (Topic'ler): {aktif_topicler}")

DOGRU_TOPIC_ADI = 'system-logs'
consumer.subscribe([DOGRU_TOPIC_ADI])

print(f"🎧 '{DOGRU_TOPIC_ADI}' dinleniyor...")
print(f"⚠️ (Eğer üstteki listede bu isim yoksa, Üretici başka bir odaya yazıyor demektir!)")

# --- 2. OPENSEARCH VE S3 AYARLARI ---
os_client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}], # 127.0.0.1 yerine localhost'u geri koyduk
    http_auth=('admin', 'NexusOps@2026!'),
    use_ssl=True, verify_certs=False, ssl_show_warn=False
)

s3_client = boto3.client(
    's3', endpoint_url='http://localhost:4566', # Burayı da localhost'a çektik
    aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1'
)
BUCKET_NAME = 'nexus-logs-bucket'

# --- 4. GÜVENLİ VERİ AKIŞI DÖNGÜSÜ ---
for message in consumer:
    try:
        raw_data = message.value.decode('utf-8')
        log_id = str(uuid.uuid4())

        try:
            log_data = json.loads(raw_data)
        except:
            log_data = {"message": raw_data}

            # A) OpenSearch'e Yaz (Eğer ulaşılamazsa sessizce geçmesini söyledik)
        try:
            os_client.index(index="nexus-logs-index", body=log_data)
            os_status = "✅"
        except Exception as os_e:
            os_status = f"❌ (OS Hata: {os_e})"

        # B) S3'e Yedekle
        try:
            s3_client.put_object(Bucket=BUCKET_NAME, Key=f"logs/backup_{log_id}.json", Body=json.dumps(log_data))
            s3_status = "✅"
        except Exception as s3_e:
            s3_status = f"❌ (S3 Hata: {s3_e})"

        print(f"Log İşlendi: OpenSearch {os_status} | S3 Bulut {s3_status} | ID: {log_id[:8]}")

    except Exception as e:
        print(f"❌ Beklenmeyen Hata: {e}")