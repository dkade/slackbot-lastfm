class Config:
    _configuration_file = 'config.cfg'
    _config_parser = False
    _data = {}

    def __init__(self):
        pass

    @staticmethod
    def _get_config_filename():
        return Config._configuration_file

    @staticmethod
    def _load_data():
        if Config._config_parser is not False:
            return None

        from ConfigParser import RawConfigParser
        Config._config_parser = RawConfigParser()
        Config._config_parser.read(Config._get_config_filename())

    @staticmethod
    def get(section, key=None):
        try:
            Config._load_data()
            if key is None:
                return Config._get_section(section)
            else:
                return Config._config_parser.get(section, key)
        except Exception as e:
            raise e

    @staticmethod
    def _get_section(section):
        Config._data[section] = {}
        for k, v in Config._config_parser.items(section):
            Config._data[section][k] = v
        return Config._data[section]

    @staticmethod
    def get_section_keys(section):
        keys = []
        for k, v in Config._config_parser.items(section):
            keys.append(k)
        return keys
