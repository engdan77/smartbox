import time

class Logger:
    _logger = None
    _init_time = None
    _keep_last = 100
    _max_time = 1000
    log_entries = []

    @classmethod
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    @classmethod
    def get_logger(cls):
        if cls._logger:
            return cls._logger
        else:
            cls._init_time = int(time.time())
        cls._logger = cls.__new__(cls)
        return cls._logger

    def get_last_records(self):
        return self.__class__.log_entries

    def purge_records_and_reset_timer(self):
        keep_last = self.__class__._keep_last
        if len(self.__class__.log_entries) > keep_last:
            self.__class__.log_entries = self.__class__.log_entries[self.__class__._keep_last:]
        current_time = int(time.time())
        if current_time > self.__class__._init_time + self.__class__._max_time:
            self.__class__._init_time = current_time

    def info(self, message):
        current_time = int(time.time()) - self.__class__._init_time
        m = f'{current_time}: {message}'
        self.purge_records_and_reset_timer()
        self.__class__.log_entries.append(m)
        print(m)
