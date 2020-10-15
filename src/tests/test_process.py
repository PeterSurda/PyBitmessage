"""
Common reusable code for tests and tests for pybitmessage process.
"""

import os
import signal
import subprocess  # nosec
import tempfile
import time
import unittest
import traceback
try:
    import psutil
except ModuleNotFoundError:
    pass

from pybitmessage.debug import logger


def put_signal_file(path, filename):
    """Creates file, presence of which is a signal about some event."""
    with open(os.path.join(path, filename), 'wb') as outfile:
        outfile.write(str(time.time()).encode())

class TestProcessProto(unittest.TestCase):
    """Test case implementing common logic for external testing:
              it starts pybitmessage in setUpClass() and stops it in tearDownClass()
    """
    
    _process_cmd = ['pybitmessage', '-d']
    _threads_count = 15
    _files = (
        'keys.dat', 'messages.dat', 'knownnodes.dat',
        '.api_started', 'unittest.lock','singleton.lock'
    )
 
    @classmethod
    def setUpClass(cls):
        """Setup environment and start pybitmessage"""
        print("setUpClass {} start.".format(cls.__name__))
        cls.home = os.environ['BITMESSAGE_HOME'] = tempfile.gettempdir()
        put_signal_file(cls.home, 'unittest.lock')
        subprocess.call(cls._process_cmd)  # nosec
        time.sleep(5)
        cls.pid = int(cls._get_readline('singleton.lock'))
        cls.process = psutil.Process(cls.pid)
        print("setUpClass {} end.".format(cls.__name__))

    @classmethod
    def _get_readline(cls, pfile):
        pfile = os.path.join(cls.home, pfile)
        try:
            with open(pfile, 'rb') as f:
                return f.readline().strip()
        except (OSError, IOError, FileNotFoundError):
            pass

    @classmethod
    def _stop_process(cls, timeout=120):
        print("_stop_process {} sending TERM.".format(cls.__name__))
        cls.process.send_signal(signal.SIGTERM)
        try:
            print("_stop_process {} waiting after TERM.".format(cls.__name__))
            cls.process.wait(timeout)
            print("_stop_process {} wait for TERM success.".format(cls.__name__))
        except psutil.TimeoutExpired:
            print("_stop_process {} wait for TERM TimeoutExpired.".format(cls.__name__))
            return False

        return True

    @classmethod
    def _cleanup_files(cls):
        for pfile in cls._files:
            try:
                os.remove(os.path.join(cls.home, pfile))
            except OSError:
                pass

    @classmethod
    def tearDownClass(cls):
        """Ensures that pybitmessage stopped and removes files"""
        try:
            if not cls._stop_process():
                print("_stop_process {} sending KILL.".format(cls.__name__))
                cls.process.kill()
                print("_stop_process {} waiting after KILL.".format(cls.__name__))
                cls.process.wait(5)
                print("_stop_process {} wait for KILL success.".format(cls.__name__))
        except (psutil.NoSuchProcess, FileNotFoundError, AttributeError) as e:
            print("_stop_process {} wait for KILL non fatal error.".format(cls.__name__))
        except psutil.TimeoutExpired as e:
            print("_stop_process {} wait for KILL TimeoutExpired.".format(cls.__name__))
        finally:
            cls._cleanup_files()

    def _test_threads(self):
        # only count for now
        # because of https://github.com/giampaolo/psutil/issues/613
        # PyBitmessage
        #   - addressGenerator
        #   - singleWorker
        #   - SQL
        #   - objectProcessor
        #   - singleCleaner
        #   - singleAPI
        #   - Asyncore
        #   - ReceiveQueue_0
        #   - ReceiveQueue_1
        #   - ReceiveQueue_2
        #   - Announcer
        #   - InvBroadcaster
        #   - AddrBroadcaster
        #   - Downloader
        self.assertEqual(
            len(self.process.threads()), self._threads_count)


class TestProcessShutdown(TestProcessProto):
    """Separate test case for SIGTERM"""
    def test_shutdown(self):
        """Send to pybitmessage SIGTERM and ensure it stopped"""
        # longer wait time because it's not a benchmark
        self.assertTrue(
            self._stop_process(120),
            '%s has not stopped in 120 sec' % ' '.join(self._process_cmd))

    @classmethod
    def tearDownClass(cls):
        """Special teardown because pybitmessage is already stopped"""
        print("tearDownClass in {}, is_running: {}".format(cls.__name__, cls.process.is_running()))
        cls._cleanup_files()


class TestProcess(TestProcessProto):
    """A test case for pybitmessage process"""
    def test_process_name(self):
        """Check PyBitmessage process name"""
        self.assertEqual(self.process.name(), 'pybitmessage')

    def test_files(self):
        """Check existence of PyBitmessage files"""
        for pfile in self._files:
            if pfile.startswith('.'):
                continue
            self.assertIsNot(
                self._get_readline(pfile), None,
                'Failed to read file {}'.format(pfile)
            )

    def test_threads(self):
        """Testing PyBitmessage threads"""
        self._test_threads()
