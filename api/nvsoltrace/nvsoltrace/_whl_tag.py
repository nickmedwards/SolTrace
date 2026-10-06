import re, sysconfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        _platform_tag = re.sub(r'[-.]', '_', sysconfig.get_platform())
        # if linux clean tag for PyPi
        if _platform_tag[:5] == 'linux':
            _platform_tag = 'many' + _platform_tag
        build_data['tag'] = f'py3-none-{_platform_tag}'
        build_data['pure_python'] = False
