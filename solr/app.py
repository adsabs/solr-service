
import logging.config
from flask import Flask, make_response, jsonify
from views import StatusView, Tvrh, Search, Qtree, BigQuery
from flask.ext.restful import Api
from flask.ext.discoverer import Discoverer
from flask.ext.consulate import Consul, ConsulConnectionError


def create_app():
    """
    Application factory
    :return configured flask.Flask application instance
    """
    app = Flask(__name__, static_folder=None)

    app.url_map.strict_slashes = False
    Consul(app)  # load_config expects consul to be registered
    load_config(app)
    logging.config.dictConfig(
        app.config['SOLR_SERVICE_LOGGING']
    )
    
    api = Api(app)

    @api.representation('application/json')
    def json(data, code, headers):
        """
        Since we force SOLR to always return JSON, it is faster to
        return JSON as text string directly, without parsing and serializing
        it multiple times
        """
        if not isinstance(data, basestring):
            resp = jsonify(data)
            resp.status_code = code
        else:
            resp = make_response(data, code)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Server'] = 'Solr Microservice {v}'.format(
            v=app.config.get('SOLR_SERVICE_VERSION')
        )
        if code == 200:
            resp.headers['Cache-Control'] = app.config.get('SOLR_CACHE_CONTROL', "public, max-age=600")
        return resp

    api.add_resource(StatusView, '/status')
    api.add_resource(Tvrh, '/tvrh')
    api.add_resource(Search, '/query')
    api.add_resource(Qtree, '/qtree')
    api.add_resource(BigQuery, '/bigquery')

    Discoverer(app)
    return app


def load_config(app):
    """
    Loads configuration in the following order:
        1. config.py
        2. local_config.py (ignore failures)
        3. consul (ignore failures)
    :param app: flask.Flask application instance
    :return: None
    """

    app.config.from_pyfile('config.py')

    try:
        app.config.from_pyfile('local_config.py')
    except IOError:
        app.logger.warning("Could not load local_config.py")
    try:
        app.extensions['consul'].apply_remote_config()
    except ConsulConnectionError, e:
        app.logger.warning("Could not apply config from consul: {}".format(e))


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
