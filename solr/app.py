from flask import Flask, make_response, jsonify
from flask.ext.restful import Api
from flask.ext.discoverer import Discoverer
from flask.ext.consulate import Consul, ConsulConnectionError
from flask.ext.sqlalchemy import SQLAlchemy
from views import StatusView, Tvrh, Search, Qtree, BigQuery
from adsmutils import ADSFlask

def create_app(**config):
    """
    Application factory
    :return configured flask.Flask application instance
    """
    if config:
        app = ADSFlask(__name__, static_folder=None, local_config=config)
    else:
        app = ADSFlask(__name__, static_folder=None)

    app.url_map.strict_slashes = False

    ## pysqlite driver breaks transactions, we have to apply some hacks as per
    ## http://docs.sqlalchemy.org/en/rel_0_9/dialects/sqlite.html#pysqlite-serializable

    if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', None):
        from sqlalchemy import event
        engine = app.db.engine

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
        if 'Set-Cookie' in headers:
            resp.headers['Set-Cookie'] = headers['Set-Cookie']
        return resp

    api.add_resource(StatusView, '/status')
    api.add_resource(Tvrh, '/tvrh')
    api.add_resource(Search, '/query')
    api.add_resource(Qtree, '/qtree')
    api.add_resource(BigQuery, '/bigquery')

    Discoverer(app)
    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
