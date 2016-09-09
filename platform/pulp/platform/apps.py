from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import apps


class PulpPlatformConfig(apps.AppConfig):
    name = 'pulp.platform'
    label = 'pulp_platform'
