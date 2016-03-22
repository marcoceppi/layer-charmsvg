
import os
import shutil
import tarfile

from charms import apt
from charms import nginxlib
from charms.reactive import when, when_not, set_state, remove_state
from charms.layer import charmsvg

from charmhelpers.core import hookenv


@when_not('charm-svg.installed')
@when_not('apt.queued_installs')
def install_charmsvg():
    apt.queue_install([
        'python-bottle',
        'python-yaml',
        'python-networkx',
        'python-requests',
    ])


@when('apt.installed.python-bottle')
@when_not('charm-svg.installed')
def install_resource():
    remove_state('charm-svg.ready')
    hookenv.status_set('maintenance', 'extracting resources')

    svg_bin = hookenv.resource_get('python-jujusvg')
    web_tar = hookenv.resource_get('webapp')

    hookenv.status_set('maintenance', 'installing python-jujusvg')

    shutil.copy(svg_bin, charmsvg.JUJUSVG_PATH)
    os.chmod(charmsvg.JUJUSVG_PATH, 0o755)

    hookenv.status_set('maintenance', 'installing webapp')

    tar = tarfile.open(web_tar)
    tar.extractall(charmsvg.INSTALL_PATH)
    chownr(charmsvg.INSTALL_PATH, 'ubuntu', 'ubuntu')

    set_state('charm-svg.installed')


@when('charm-svg.installed')
@when_not('charm-svg.ready')
def configure_charmsvg():
    remove_state('charm-svg.running')
    hookenv.status_set('maintenance', 'configuring webapp')

    with open(charmsvg.SETTINGS_PATH, 'w') as f:
        f.write("JUJSVG = '%s'\nPORT = %s" % (charmsvg.JUJUSVG_PATH, 80))

    set_state('charm-svg.ready')


@when('charm-svg.ready')
@when_not('charm-svg.running')
def start_charmsvg():
    hookenv.status_set('maintenance', 'starting charm-svg')
    is_ready()


@when('nginx.available')
@when('charm-svg.running')
def create_vhost():
    nginxlib.configure_site('charmsvg', 'charmsvg-vhost.conf',
        server_name='_',
        source_path=charmsvg.INSTALL_PATH,
    )

    open_port(80)
    status_set('active', 'ready')


@hook('update-status')
def is_ready():
    if is_state('charm-svg.running'):
        hookenv.status_set('active', 'running on port 80')


@hook('upgrade-charm')
def upgrade():
    """ Upgrade charm or resources

    This method will assume both resource or charm is being upgraded. As such
    this will reset the charm-svg.installed state which will re-kick the setup
    and configuration portions of the charm.

    Future updates to this method may include removing additional events to
    better handle upgrades.

    """

    remove_state('charm-svg.installed')
    remove_state('charm-svg.ready')


def chownr(path, uid, gid):
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)
