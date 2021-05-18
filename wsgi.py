from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from solr import app

application = app.create_app()

if __name__ == "__main__":
    run_simple('0.0.0.0', 4000, application, use_reloader=False, use_debugger=True)

