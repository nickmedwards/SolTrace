from pathlib import Path
import orjson

from pysoltrace import dot_h
from pysoltrace.api.utils import st_function
from pysoltrace.api.dll import context

##############################################################
# functions for simulation data management thru json strings #
##############################################################
class json(context):
    @st_function
    def load(self, input_json: str | dict | Path) -> None:
        assert isinstance(input_json, (str, dict, Path)), f'input_json must be a str, dict, or Path, got {type(input_json)}'

        loader = self._pdll.st_read_input_json
        if isinstance(input_json, str):
            f = open(input_json, mode='rb')
            _json = f.read()
            f.close()
        elif isinstance(input_json, dict):
            _json = orjson.dumps(input_json)
        else:
            _json = str(input_json.resolve()).encode('utf-8')
            loader = self._pdll.st_read_input_json_file

        return loader(self._pcxt, _json)

    @st_function
    def dump(self, filename: str):
        return self._pdll.st_export_json_file(self._pcxt, filename.encode())