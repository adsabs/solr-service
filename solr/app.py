
import logging.config
from flask import Flask, make_response, jsonify
from flask.ext.restful import Api
from flask.ext.discoverer import Discoverer
from flask.ext.consulate import Consul, ConsulConnectionError
from flask.ext.sqlalchemy import SQLAlchemy
from views import StatusView, Tvrh, Search, Qtree, BigQuery

db = SQLAlchemy()

def create_app(**config):
    """
    Application factory
    :return configured flask.Flask application instance
    """
    app = Flask(__name__, static_folder=None)

    app.url_map.strict_slashes = False
    Consul(app)  # load_config expects consul to be registered
    load_config(app)
    if config:
        app.config.update(config)
        
    db.init_app(app)
    logging.config.dictConfig(
        app.config['SOLR_SERVICE_LOGGING']
    )
    
    ## pysqlite driver breaks transactions, we have to apply some hacks as per
    ## http://docs.sqlalchemy.org/en/rel_0_9/dialects/sqlite.html#pysqlite-serializable
    
    if 'sqlite' in (app.config.get('SQLALCHEMY_BINDS') or {'solr_service':''})['solr_service']:
        from sqlalchemy import event
        
        binds = app.config.get('SQLALCHEMY_BINDS')
        if binds and 'solr_service' in binds:
            engine = db.get_engine(app, bind=(app.config.get('SQLALCHEMY_BINDS') and 'solr_service'))
        else:
            engine = db.get_engine(app)
        
        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @event.listens_for(engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.execute("BEGIN")
    
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
