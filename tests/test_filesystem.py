from hamcrest import *
from myna import shim
import stat
import unittest
from fuse import FuseOSError

from kubefuse.client import KubernetesClient
from kubefuse.path import KubePath
from kubefuse.filesystem import KubeFileSystem

tmpdir = None

def setUp():
    global tmpdir
    tmpdir = shim.setup_shim_for('kubectl')	

def tearDown():
    global tmpdir
    shim.teardown_shim_dir(tmpdir)

class KubeFileSystemTest(unittest.TestCase):
    def test_getattr_for_namespace(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/default')
        fs = KubeFileSystem(path)
        attr = fs.getattr(client)
        assert_that(attr['st_mode'], is_(stat.S_IFDIR | 0555))
        assert_that(attr['st_nlink'], is_(2))
        assert_that(attr['st_size'], is_(0))
        # NB. time not tested, but whatever

    def test_getattr_for_resource(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/default/pod')
        fs = KubeFileSystem(path)
        attr = fs.getattr(client)
        assert_that(attr['st_mode'], is_(stat.S_IFDIR | 0555))
        assert_that(attr['st_nlink'], is_(2))
        assert_that(attr['st_size'], is_(0))
        # NB. time not tested, but whatever

    def test_getattr_for_object(self):
        client = KubernetesClient()
        pod = client.get_pods()[0]
        path = KubePath().parse_path('/default/pod/%s' % pod)
        fs = KubeFileSystem(path)
        attr = fs.getattr(client)
        assert_that(attr['st_mode'], is_(stat.S_IFDIR | 0555))
        assert_that(attr['st_nlink'], is_(2))
        assert_that(attr['st_size'], is_(0))
        # NB. time not tested, but whatever

    def test_getattr_for_action(self):
        client = KubernetesClient()
        pod = client.get_pods()[0]
        path = KubePath().parse_path('/default/pod/%s/describe' % pod)
        fs = KubeFileSystem(path)
        attr = fs.getattr(client)
        assert_that(attr['st_mode'], is_(stat.S_IFREG | 0444))
        assert_that(attr['st_nlink'], is_(1))
        assert_that(attr['st_size'], is_(50000))
        # NB. time not tested, but whatever

    def test_getattr_for_nonexistent_path(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/doesnt-exist')
        fs = KubeFileSystem(path)
        assert_that(calling(lambda: fs.getattr(client)), raises(FuseOSError))

    def test_list_files_for_root(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/')
        fs = KubeFileSystem(path)
        files = fs.list_files(client)
        namespaces = client.get_namespaces()
        assert_that(files, contains(*namespaces))
        assert_that(len(files), is_(len(namespaces)))

    def test_list_files_for_namespace(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/default')
        fs = KubeFileSystem(path)
        files = fs.list_files(client)
        assert_that(files, contains('pod', 'svc', 'rc'))
        assert_that(len(files), is_(3))

    def test_list_files_for_resource(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/default/pod')
        fs = KubeFileSystem(path)
        files = fs.list_files(client)
        pods = client.get_pods()
        assert_that(files, contains(*pods))
        assert_that(len(files), is_(len(pods)))

    def test_list_files_for_object(self):
        client = KubernetesClient()
        pod = client.get_pods()[0]
        path = KubePath().parse_path('/default/pod/%s' % pod)
        fs = KubeFileSystem(path)
        files = fs.list_files(client)
        assert_that(files, has_items('describe', 'logs', 'json', 'yaml'))
        assert_that(len(files), is_(4))

    def test_list_files_for_file_throws_exception(self):
        client = KubernetesClient()
        pod = client.get_pods()[0]
        path = KubePath().parse_path('/default/pod/%s/describe' % pod)
        fs = KubeFileSystem(path)
        assert_that(calling(lambda: fs.list_files(client)), raises(FuseOSError))

    def test_list_files_for_nonexistent_path(self):
        client = KubernetesClient()
        path = KubePath().parse_path('/doesnt-exist')
        fs = KubeFileSystem(path)
        assert_that(calling(lambda: fs.list_files(client)), raises(FuseOSError))
