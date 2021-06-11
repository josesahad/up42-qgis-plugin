"""
Module containing parameters and settings for Sentinel Hub services
"""

from PyQt5.QtCore import QSettings, QObject


class Settings(QObject):
    """ A class in charge of all settings. It also handles loading and saving of settings to QGIS settings store
    """

    _STORE_NAMESPACE = 'UP42'

    _FIELDS = [
        'project_id',
        'project_api_key',
        'download_folder'
    ]

    project_id = None
    project_api_key = None
    download_folder = None

    _initialized = False

    def __init__(self):
        super(Settings, self).__init__()
        self.q_settings = QSettings()
        for field in self._FIELDS:
            path = self._get_store_path(field)
            value = self.q_settings.value(path, '')
            object.__setattr__(self, field, value)
        self._initialized = True

    def __setattr__(self, key, value):
        super(Settings, self).__setattr__(key, value)
        if self._initialized:
            self.sync()

    def sync(self):
        for field in self._FIELDS:
            path = self._get_store_path(field)
            value = getattr(self, field)
            self.q_settings.setValue(path, value)
            # print(f"setting set: {path}={value}")

    def _get_store_path(self, parameter_name):
        """ Provides a location of the parameter in the local store
        """
        return '{}/{}'.format(self._STORE_NAMESPACE, parameter_name)
