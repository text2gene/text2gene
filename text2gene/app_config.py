from __future__ import absolute_import, print_function

import os
from configparser import NoSectionError

from flask import Flask, render_template
from flask_basicauth import BasicAuth

from .base_routes import base
from .routes_v1.routes import routes_v1
from .config import CONFIG

app = Flask(__name__,
            static_folder=os.path.join(os.getcwd(), 'text2gene', 'static'),
            static_url_path='',
            template_folder=os.path.join(os.getcwd(), 'text2gene', 'templates'),
            )
app.config['DEBUG'] = False

# if a basic_auth section is found and filled out in the config,
# set up Flask BasicAuth with configured username and passsword.
try:
    if CONFIG.get('basicauth', 'username'):
        app.config['BASIC_AUTH_USERNAME'] = CONFIG.get('basicauth', 'username')
        app.config['BASIC_AUTH_PASSWORD'] = CONFIG.get('basicauth', 'password')
        basic_auth = BasicAuth(app)
        app.config['BASIC_AUTH_FORCE'] = True
except NoSectionError:
    pass

app.register_blueprint(base)
app.register_blueprint(routes_v1)

# Define existing routes and pass it to the template, to create a list.
# 
# app.url_map looks like this:
"""app.url_map
Out[3]: 
Map([<Rule '/v1/echo' (HEAD, OPTIONS, GET) -> routes_v1.echo>,
 <Rule '/v2/echo' (HEAD, OPTIONS, GET) -> routes_v2.echo>,
 <Rule '/routes/' (HEAD, OPTIONS, GET) -> routes>,
 <Rule '/about' (HEAD, OPTIONS, GET) -> base.about>,
 <Rule '/OK' (HEAD, OPTIONS, GET) -> base.OK>,
 <Rule '/' (HEAD, OPTIONS, GET) -> base.home>,
 <Rule '/<filename>' (HEAD, OPTIONS, GET) -> static>])"""

@app.route('/routes/')
def routes():
    post_routes = []
    get_routes = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods:
            get_routes.append(rule)     #.rule)
        if "POST" in rule.methods:
            post_routes.append(rule)    #.rule)

    return render_template('routes.html', get_routes=get_routes, post_routes=post_routes)

