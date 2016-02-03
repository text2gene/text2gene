import json
import datetime

import pytz
from pyrfc3339 import generate, parse

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# The following helper classes assist in datetime conversion between Python and JSON. 
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return generate(obj.replace(tzinfo=pytz.utc))
        else:
            return str(obj)
        return json.JSONEncoder.default(self, obj)

class CustomJsonDecoder(json.JSONDecoder):
    def decode(self, json_string):
        obj = super(CustomJsonDecoder,self).decode(json_string)
        for k, v in obj.items():
            try:
                obj[k] = parse(v)
            except ValueError:
                pass
        return obj

