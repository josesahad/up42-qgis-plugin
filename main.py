"""
The main module
"""

import tempfile
from dataclasses import dataclass

import up42
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject, QgsRasterLayer

from .dockwidget import UP42DockWidget
from .settings import Settings

PLUGIN_NAME = "UP42"


@dataclass
class Job:
    id: str
    name: str
    instance: object


class UP42Plugin:
    """ The main class defining the high-level plugin logic and interactions with UI

    The methods that are called externally by QGIS are:
      - __init__
      - initGui
      - unload

    Any other public method is connected to UI and can be triggered by a user's action in QGIS. Non-public methods are
    the ones that are only called by other methods.
    """

    # pylint: disable=too-many-public-methods

    # ICON_PATH = ':/plugins/UP42/favicon.ico'

    def __init__(self, iface):
        """ Called by QGIS at the beginning when you open QGIS or when the plugin is enabled in the
        Plugin Manager.

        :param iface: A QGIS interface instance, it is the same object as qgis.utils.iface
        :type iface: QgsInterface
        """
        self.iface = iface
        self.toolbar = self.iface.addToolBar("UP42")
        self.plugin_actions = []
        self.dockwidget = None

        self.settings = Settings()
        self.manager = None

        self._default_layer_selection_event = None

    @staticmethod
    def download_qgis_layer(out_path: str, name_layer: str = "Layer"):
        """ Uploads an image into QGis
        """
        # get the path to a tif file  e.g. /home/project/data/srtm.tif
        # TODO change name
        output_layer = QgsRasterLayer(out_path, name_layer)
        if not output_layer.isValid():
            print("Layer failed to load!")

        QgsProject.instance().addMapLayer(output_layer)

    def get_job_results(self):
        """ Uploads an image into QGis
        """
        temp_dir_path = tempfile.mkdtemp(prefix="output_", dir=self.settings.download_folder)
        job_id = self.dockwidget.jobsComboBox.currentData()

        up42.authenticate(project_id=self.settings.project_id,
                          project_api_key=self.settings.project_api_key)
        job = up42.initialize_job(job_id)
        out_path = job.download_results(output_directory=temp_dir_path, unpacking=True)

        self.download_qgis_layer(out_path=out_path[0], name_layer=job_id)  # TODO attention several paths are output

    def _fetch_jobs(self):
        up42.authenticate(project_id=self.settings.project_id,
                          project_api_key=self.settings.project_api_key)
        project = up42.initialize_project()
        jobs_collection = project.get_jobs(return_json=False, test_jobs=False, real_jobs=True)

        return [Job(j.job_id, j.info['name'], j) for j in jobs_collection]

    def update_jobs_combo(self):
        print('update_jobs_combo()')
        jobs = self._fetch_jobs()
        # jobs = []
        for j in jobs:
            label = f"{j.name} ({j.id})"
            self.dockwidget.jobsComboBox.addItem(label, j.id)

    def initGui(self):
        """ This method is called by QGIS when the main GUI starts up or when the plugin is enabled in the
        Plugin Manager.
        """
        action = QAction('../UP42', self.iface.mainWindow())

        # icon = QIcon(self.ICON_PATH)
        # bold_plugin_name = '<b>{}</b>'.format("UP42")
        # action = QAction(icon, bold_plugin_name, self.iface.mainWindow())

        action.triggered.connect(self.run)
        action.setEnabled(True)

        self.toolbar.addAction(action)
        self.iface.addPluginToWebMenu("UP42", action)

        self.plugin_actions.append(action)

    def unload(self):
        """ This is called by QGIS when a user disables or uninstalls the plugin. This method removes the plugin and
        it's icon from everywhere it appears in QGIS GUI.
        """
        if self.dockwidget:
            self.dockwidget.close()

        for action in self.plugin_actions:
            self.iface.removePluginWebMenu(
                PLUGIN_NAME,
                action
            )
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def update_project_id(self):
        print('update_project_id()')
        self.settings.project_id = self.dockwidget.projectId.text()

    def update_project_api_key(self):
        print('update_project_api_key()')
        self.settings.project_api_key = self.dockwidget.projectApiKey.text()

    def update_download_folder(self):
        print('update_download_folder()')
        self.settings.download_folder = self.dockwidget.downloadFolder.text()

    def run(self):
        """ It loads and starts the plugin and binds all UI actions.
        """
        if self.dockwidget is not None:
            return

        self.dockwidget = UP42DockWidget()
        self.dockwidget.setWindowTitle('{} plugin v{}'.format("UP42", "1.0.0"))
        self.initialize_ui()

        # Close event
        self.dockwidget.closingPlugin.connect(self.on_close_plugin)

        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

    def initialize_ui(self):
        """ Initializes and resets entire UI
        """
        # Listen to events
        self.dockwidget.projectId.editingFinished.connect(self.update_project_id)
        self.dockwidget.projectApiKey.editingFinished.connect(self.update_project_api_key)
        self.dockwidget.downloadFolder.editingFinished.connect(self.update_download_folder)

        self.dockwidget.fetchJobsPushButton.clicked.connect(self.update_jobs_combo)
        self.dockwidget.downloadJobPushButton.clicked.connect(self.get_job_results)

        # Set field content
        self.dockwidget.projectId.setText(self.settings.project_id)
        self.dockwidget.projectApiKey.setText(self.settings.project_api_key)
        self.dockwidget.downloadFolder.setText(self.settings.download_folder)

    def on_close_plugin(self):
        """ Cleanup necessary items here when a close event on the dockwidget is triggered

        Note that all connections to the QGIS interface have to be cleaned here.
        """
        self.dockwidget.closingPlugin.disconnect(self.on_close_plugin)
        self.dockwidget = None
