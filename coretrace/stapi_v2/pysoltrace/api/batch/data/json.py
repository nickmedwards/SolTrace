import ctypes
from pathlib import Path
import orjson

from pysoltrace import dot_h
from pysoltrace.api.batch.utils import batcher, generate_api_call

##############################################################
# functions for simulation data management thru json strings #
##############################################################
class json(batcher):
    def load(self, input_json: str | dict) -> None:
        # TODO: add Path arg for filename
        assert isinstance(input_json, (str, dict, Path)), \
            f'input_json must be a str, dict, or Path, got {type(input_json)}'

        loader = dot_h.st_api_call.CALL_ST_READ_INPUT_JSON
        if isinstance(input_json, str):
            f = open(input_json, mode='rb')
            _json = f.read()
            f.close()
        elif isinstance(input_json, dict):
            _json = orjson.dumps(input_json)
        # TODO: implement below
        # else:
        #     _json = input_json.name.encode('utf-8')
        #     loader = dot_h.st_api_call.CALL_ST_READ_INPUT_JSON_by_name

        return self.adder(generate_api_call(loader, _json))

    def dump(self, filename: str):
        return self.adder(generate_api_call(dot_h.st_api_call.CALL_ST_EXPORT_JSON_FILE,
                                            filename.encode()))