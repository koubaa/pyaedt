# Setup paths for module imports
from _unittest.conftest import scratch_path
from _unittest.conftest import desktop_init
import gc
import tempfile
import os
import io
import sys

# Import required modules
from pyaedt import Hfss
from pyaedt.generic.filesystem import Scratch
from pyaedt.aedt_logger import AedtLogger


class TestClass:
    def setup_class(self, close_projects):
        # set a scratch directory and the environment / test data
        #desktop.release_desktop(close_projects=True, close_on_exit=False)
        breakpoint()
        desktop_init.release_desktop(close_projects=True, close_on_exit=False)

        with Scratch(scratch_path) as self.local_scratch:
            self.aedtapp = Hfss(new_desktop_session=True)

    def teardown_class(self):
        assert self.aedtapp.close_project(self.aedtapp.project_name)
        self.local_scratch.remove()
        gc.collect()

    def test_01_global(self):
        logger = self.aedtapp.logger
        # The default logger level is DEBUGGING.
        logger.glb.debug("Debug message for testing.")
        logger.glb.info("Info message for testing.")
        logger.glb.warning("Warning message for testing.")
        logger.glb.error("Error message for testing.")
        logger.glb.info("Critical message for testing.")

        # Project logger
        logger.add_logger("Project")
        logger.project.debug("Debug message for testing.")
        logger.project.info("Info message for testing.")
        logger.project.warning("Warning message for testing.")
        logger.project.error("Error message for testing.")
        logger.project.info("Critical message for testing.")

        # Current active design logger
        logger.add_logger("Design")
        logger.design.debug("Debug message for testing.")
        logger.design.info("Info message for testing.")
        logger.design.warning("Warning message for testing.")
        logger.design.error("Error message for testing.")
        logger.design.info("Critical message for testing.")

        global_messages = logger.get_messages().global_level
        assert len(global_messages) == 11
        assert global_messages[0] == '[info] pyaedt v0.4.dev0'
        assert '[info] Python version 3.8.0' in global_messages[1]
        assert '[info] Project' in global_messages[2]
        assert '[info] No design is present. Inserting a new design.' in global_messages
        assert '[info] Design Loaded' in global_messages
        assert '[info] Materials Loaded' in global_messages
        assert '[info] Debug message for testing.' in global_messages
        assert '[info] Info message for testing.' in global_messages
        assert '[warning] Warning message for testing.' in global_messages
        assert '[error] Error message for testing.' in global_messages
        assert '[info] Critical message for testing.' in global_messages

        design_messages = logger.get_messages().design_level
        assert len(design_messages) == 6
        assert '[info] Successfully loaded project materials !' in design_messages[0]
        assert '[info] Debug message for testing.' in design_messages[1]
        assert '[info] Info message for testing.' in design_messages[2]
        assert '[warning] Warning message for testing.' in design_messages[3]
        assert '[error] Error message for testing.' in design_messages[4]
        assert '[info] Critical message for testing.' in design_messages[5]

        project_messages = logger.get_messages().project_level
        assert len(project_messages) == 5
        assert '[info] Debug message for testing.' in project_messages[0]
        assert '[info] Info message for testing.' in project_messages[1]
        assert '[warning] Warning message for testing.' in project_messages[2]
        assert '[error] Error message for testing.' in project_messages[3]
        assert '[info] Critical message for testing.' in project_messages[4]

        logger.clear_messages("", "", 2)
        #assert not logger.get_messages().global_level

    def test_02_output_file_with_app_filter(self):
        content = None
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.txt")
            logger = AedtLogger(self.aedtapp._messenger, filename=path)
            logger.glb.info("Info for Global")
            logger.glb.debug("Debug for Global")
            logger.glb.warning("Warning for Global")
            logger.glb.error("Error for Global")
            project_logger = logger.add_logger('Project')
            project_logger.info("Info for Project")
            project_logger.debug("Debug for Project")
            project_logger.warning("Warning for Project")
            project_logger.error("Error for Project")
            design_logger = logger.add_logger('Design')
            design_logger.info("Info for Design")
            design_logger.debug("Debug for Design")
            design_logger.warning("Warning for Design")
            design_logger.error("Error for Design")

            # Close every handlers to make sure that the 
            # file handler on every logger has been released properly.
            # Otherwise, we can't read the content of the log file.
            for handler in logger.glb.handlers:
                handler.close()
            for handler in project_logger.handlers:
                handler.close()
            for handler in design_logger.handlers:
                handler.close()

            with open(path, 'r') as f:
                content = f.readlines()

        assert ":Global:INFO    :Info for Global" in content[0]
        assert ":Global:DEBUG   :Debug for Global" in content[1]
        assert ":Global:WARNING :Warning for Global" in content[2]
        assert ":Global:ERROR   :Error for Global" in content[3]
        assert ":INFO    :Info for Project" in content[4]
        assert ":DEBUG   :Debug for Project" in content[5]
        assert ":WARNING :Warning for Project" in content[6]
        assert ":ERROR   :Error for Project" in content[7]
        assert ":INFO    :Info for Design" in content[8]
        assert ":DEBUG   :Debug for Design" in content[9]
        assert ":WARNING :Warning for Design" in content[10]
        assert ":ERROR   :Error for Design" in content[11]

        self.aedtapp.logger.glb.handlers.pop()
        self.aedtapp.logger.project.handlers.pop()
        self.aedtapp.logger.design.handlers.pop()


    def test_03_stdout_with_app_filter(self):
        capture = CaptureStdOut()
        with capture:
            logger = AedtLogger(self.aedtapp._messenger, to_stdout=True)
            logger.glb.info("Info for Global")
            logger.glb.debug("Debug for Global")
            logger.glb.warning("Warning for Global")
            logger.glb.error("Error for Global")
            project_logger = logger.add_logger('Project')
            project_logger.info("Info for Project")
            project_logger.debug("Debug for Project")
            project_logger.warning("Warning for Project")
            project_logger.error("Error for Project")
            design_logger = logger.add_logger('Design')
            design_logger.info("Info for Design")
            design_logger.debug("Debug for Design")
            design_logger.warning("Warning for Design")
            design_logger.error("Error for Design")

        assert "PyAEDT Info: Info for Global" in capture.content
        assert "PyAEDT Info: Debug for Global" in capture.content
        assert "PyAEDT Warning: Warning for Global" in capture.content
        assert "PyAEDT Error: Error for Global" in capture.content
        assert "PyAEDT Info: Info for Project" in capture.content
        assert "PyAEDT Info: Debug for Project" in capture.content
        assert "PyAEDT Warning: Warning for Project" in capture.content
        assert "PyAEDT Error: Error for Project" in capture.content
        assert "PyAEDT Info: Info for Design" in capture.content
        assert "PyAEDT Info: Debug for Design" in capture.content
        assert "PyAEDT Warning: Warning for Design" in capture.content
        assert "PyAEDT Error: Error for Design" in capture.content

        for handler in logger.glb.handlers:
            handler.close()
        for handler in project_logger.handlers:
            handler.close()
        for handler in design_logger.handlers:
            handler.close()


class CaptureStdOut():
    """Capture standard output with a context manager."""

    def __init__(self):
        self._stream = io.StringIO()

    def __enter__(self):
        sys.stdout = self._stream

    def __exit__(self, type, value, traceback):
        sys.stdout = sys.__stdout__

    @property
    def content(self):
        """Return the captured content."""
        return self._stream.getvalue()