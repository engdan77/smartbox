# from umqtt2.simple2 import MQTTClient
from mqtt import MQTTClient
from mylogger import Logger

logger = Logger.get_logger()


def publish(client='umqtt_client', broker='127.0.0.1', topic='/mytopic/foo', message='', username=None, password=None):
    logger.info(f'MQTT publish, broker: {broker}, topic: {topic}, message: {message}, username: {username}, password: {password}')
    c = MQTTClient(client, broker, user=username, password=password)
    try:
        c.connect()
    except OSError as e:
        print('unable to connect to mqtt {} with error {}'.format(broker, e))
    else:
        # has to be bytes
        logger.attempt(f'try to publish {message}')
        c.publish(str(topic).encode(), str(message).encode())
        c.disconnect()
    logger.info('MQTT sent')
