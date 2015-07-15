from flask import Flask, make_response, jsonify
from views import StatusView, Tvrh, Search, Qtree, BigQuery
from flask.ext.restful import Api
from flask.ext.discoverer import Discoverer


def create_app():
    app = Flask(__name__, static_folder=None)

    app.url_map.strict_slashes = False
    app.config.from_pyfile('config.py')
    try:
        app.config.from_pyfile('local_config.py')
    except IOError:
        pass

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
        resp.headers['Cache-Control'] = "public, max-age=6000"
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
