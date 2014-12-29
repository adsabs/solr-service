import os
from flask import Blueprint
from flask import Flask, g
from views import blueprint
from views import StatusView, Resources, Tvrh, Search, Qtree
from flask.ext.restful import Api

def create_app(blueprint_only=False):
  app = Flask(__name__, static_folder=None) 

  app.url_map.strict_slashes = False
  app.config.from_pyfile('config.py')
  try:
    app.config.from_pyfile('local_config.py')
  except IOError:
    pass

  api = Api(blueprint)
  api.add_resource(StatusView,'/status')
  api.add_resource(Resources,'/resources')  
  api.add_resource(Tvrh,'/tvrh')
  api.add_resource(Search,'/search')
  api.add_resource(Qtree,'/qtree')


  if blueprint_only:
    return blueprint
  app.register_blueprint(blueprint)
  return app

if __name__ == "__main__":
  app = create_app()
  app.run(debug=True)
