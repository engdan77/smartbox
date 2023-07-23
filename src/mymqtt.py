# from umqtt2.simple2 import MQTTClient
from mqtt import MQTTClient
from mylogger import Logger

logger = Logger.get_logger()


def publish(client='umqtt_client', broker='127.0.0.1', topic='/mytopic/foo', message='', username=None, password=None):
    logger.info(f'MQTT publish, broker: {broker}, topic: {topic}, message: {message}, username: {username}, password: {password}')
    c = MQTTClient(client, broker, user=username, password=password)
    try:
        logger.info(f'MQTT connecting to {broker}')
        c.connect()
    except OSError as e:
        print('unable to connect to mqtt {} with error {}'.format(broker, e))
    else:
        # has to be bytes
        logger.info(f'MQTT try to publish {message}')
        c.publish(topic, str(message))
        c.disconnect()
    logger.info('MQTT sent')
