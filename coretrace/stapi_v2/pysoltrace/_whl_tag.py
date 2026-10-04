import re, sysconfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        _platform_tag = re.sub(r'[-.]', '_', sysconfig.get_platform())
        build_data['tag'] = f'py3-none-{_platform_tag}'
