from __future__ import absolute_import, print_function

from functools import wraps
import getpass

import os, json, logging
from datetime import datetime
import pytz
from pyrfc3339 import generate, parse

from flask import Response, make_response, request, abort

log = logging.getLogger('text2gene.http')

#TODO: make configurable from config file
ALLOWED_IPS = ['50.0.191.24']

def restrict_by_ip(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if request.remote_addr in ALLOWED_IPS:
            return func(*args, **kwargs)
        else:
            return abort(403, 'IP address %s cannot access this part of the API' % request.remote_addr)
    return wrapped

def get_hostname():
    hostname = getpass.os.uname()[1]
    return hostname

def HTTP200(serializable):
    #log.debug('[HTTP_200] '+str(serializable))
    try:
        return Response(json.dumps(serializable, cls=CustomJsonEncoder), status=200, mimetype='application/json')
    except UnicodeDecodeError:
        # make an attempt to correct 
        message = unicode(json.dumps(serializable), "ISO-8859-1")
        return Response(message, status=200, mimetype='application/json')

def HTTP400(err, errorMessage='Error'):
    log.error('[HTTP_400] error while %s: %s', errorMessage, err)
    return Response(json.dumps({str(errorMessage): str(err)}), status=400, mimetype='application/json')

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

