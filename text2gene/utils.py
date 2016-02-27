from __future__ import absolute_import, print_function

import os, json, logging
from datetime import datetime
import pytz
from pyrfc3339 import generate, parse

from flask import Response, make_response

log = logging.getLogger('library-services')

import getpass
def get_hostname():
    hostname = getpass.os.uname()[1]
    return hostname

def HTTP200(serializable):
    log.debug('[HTTP_200] '+str(serializable))
    try:
        return Response(json.dumps(serializable, cls=CustomJsonEncoder), status=200, mimetype='application/json')
    except UnicodeDecodeError:
        # make an attempt to correct 
        message = unicode(json.dumps(serializable), "ISO-8859-1")
        return Response(message, status=200, mimetype='application/json')

def HTTP400(e, errorMessage='Error'):
    log.error('[HTTP_400] error while %s: %s', errorMessage, e)
    return Response(json.dumps({str(errorMessage): str(e)}), status=400, mimetype='application/json')

def HTTP200_file(content, filename):
    # create a response out of the content string
    response = make_response(content)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

# The following helper class assist in datetime conversion between Python and JSON. 
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'strftime'):
            try:
                return generate(obj.replace(tzinfo=pytz.utc))
            except TypeError:
                # a time-zone-less date. 
                return datetime.strftime(obj, '%Y-%m-%d')
        else:
            return str(obj)
        return json.JSONEncoder.default(self, obj)

