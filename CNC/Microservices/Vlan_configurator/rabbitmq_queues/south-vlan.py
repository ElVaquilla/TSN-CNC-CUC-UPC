#!/usr/bin/env python
import pika
import time

rabbitmw_available=False
while(rabbitmw_available==False):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq-microservice'))
        channel = connection.channel()
        rabbitmw_available=True
    except:
        print("Couldn't connect to RabbitMQ'")
        time.sleep(5)
channel.queue_declare(queue='south-vlan', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
    with open("/var/vlan.txt", "w") as text:
            text.write(body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='south-vlan', on_message_callback=callback)

channel.start_consuming()