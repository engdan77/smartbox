try:
    import ujson as json
except ImportError:
    import json

from mylogger import Logger
logger = Logger.get_logger()


def get_config(input_default_config=None, config_file='./config.json'):
    if input_default_config is None:
        input_default_config = {}
        logger.info('WARNING: No default config nor config.json')
    c = input_default_config
    try:
        c = json.loads(open(config_file).read())
    except (OSError, ValueError) as e:
        print(f'error reading config: {e}')
        if input_default_config:
            c = input_default_config
            open(config_file, 'w').write(json.dumps(c))
        else:
            print('No default config given')
    r = {k: {'true': True, 'false': False}.get(v, v) for k, v in c.items()}
    return r


def save_config(input_config, config_file='config.json'):
    if input_config:
        c = input_config
        with open(config_file, 'w') as f:
            f.write(json.dumps(c))
    else:
        print('No default config given')