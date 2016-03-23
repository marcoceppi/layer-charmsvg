
import os
import shutil
import tarfile

import nginxlib

from charms import apt

from charms.reactive import hook
from charms.reactive import when
from charms.reactive import is_state
from charms.reactive import when_not
from charms.reactive import set_state
from charms.reactive import remove_state

from charms.layer import charmsvg
from charms.layer import uwsgi

from charmhelpers.core import hookenv
from charmhelpers.core.host import chownr


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
    chownr(charmsvg.INSTALL_PATH, 'www-data', 'www-data')

    set_state('charm-svg.installed')


@when('charm-svg.installed')
@when_not('charm-svg.ready')
def configure_charmsvg():
    remove_state('charm-svg.uwsgi.configured')
    hookenv.status_set('maintenance', 'configuring webapp')

    with open(charmsvg.SETTINGS_PATH, 'w') as f:
        f.write("JUJSVG = '%s'" % charmsvg.JUJUSVG_PATH)

    set_state('charm-svg.ready')


@when('charm-svg.ready')
@when_not('charm-svg.uwsgi.configured')
def start_charmsvg():
    hookenv.status_set('maintenance', 'configuring uwsgi')
    uwsgi.configure(
        'charmsvg',
        charmsvg.INSTALL_PATH,
        plugins='python',
        cfg={'file': 'app.py'},
    )
    set_state('charm-svg.uwsgi.configured')


@when('nginx.available')
@when('charm-svg.uwsgi.configured')
@when_not('charm-svg.nginx.configured')
def create_vhost():
    nginxlib.configure_site(
        'charmsvg',
        'charmsvg-vhost.conf',
        server_name='_',
        source_path=charmsvg.INSTALL_PATH,
        socket=uwsgi.config('charmsvg').get('socket'),
    )

    hookenv.open_port(80)
    is_ready()
    set_state('charm-svg.nginx.configured')


@hook('update-status')
def is_ready():
    nginx_ready = is_state('charm-svg.nginx.configured')
    uwsgi_ready = is_state('charm-svg.uwsgi.configured')
    uwsgi_running = uwsgi.running()

    if nginx_ready and uwsgi_ready and uwsgi_running:
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
