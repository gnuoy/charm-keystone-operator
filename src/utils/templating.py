# Copyright 2021, Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from collections import defaultdict

from charmhelpers.contrib.openstack.templating import OSConfigException
from charmhelpers.contrib.openstack.templating import OSConfigRenderer

log = logging.getLogger(__name__)


class SidecarConfigRenderer(OSConfigRenderer):

    """
    This class provides a common templating system to be used by OpenStack
    sidecar charms.
    """
    def __init__(self, templates_dir, openstack_release):
        super(SidecarConfigRenderer, self).__init__(templates_dir,
                                                    openstack_release)
        self.config_to_containers = defaultdict(set)
        self.owner_info = defaultdict(set)

    def _get_template(self, template):
        """

        """
        self._get_tmpl_env()
        if not template.endswith('.j2'):
            template += '.j2'
        template = self._tmpl_env.get_template(template)
        log.debug(f'Loaded template from {template.filename}')
        return template

    def register(self, config_file, contexts, config_template=None,
                 containers=None, user=None, group=None):
        """

        """
        # NOTE(wolsen): Intentionally overriding base class to raise an error
        #  if this is accidentally used instead.
        if containers is None:
            raise ValueError('One or more containers must be provided')

        super().register(config_file, contexts, config_template)

        # Register user/group info. There's a better way to do this for sure
        if user or group:
            self.owner_info[config_file] = (user, group)

        for container in containers:
            self.config_to_containers[config_file].add(container)
            log.debug(f'Registered config file "{config_file}" for container '
                      f'{container}')

    def write(self, config_file, container):
        """

        """
        containers = self.config_to_containers.get(config_file)
        if not containers or container.name not in containers:
            log.error(f'Config file {config_file} not registered for '
                      f'container {container.name}')
            raise OSConfigException

        contents = self.render(config_file)
        owner_info = self.owner_info.get(config_file)
        kwargs = {}
        log.debug(f'Got owner_info of {owner_info}')
        if owner_info:
            user, group = owner_info
            kwargs['user'] = user
            kwargs['group'] = group
        container.push(config_file, contents, **kwargs)

        log.debug(f'Wrote template {config_file} in container '
                  f'{container.name}.')

    def write_all(self, container=None):
        for config_file, containers in self.config_to_containers.items():
            if container:
                if container.name not in containers:
                    continue

                self.write(config_file, container)
            else:
                for c in containers:
                    self.write(config_file, c)
