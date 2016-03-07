
from flask_cors import CORS
from solr.app import create_app

if __name__ == '__main__':
    app = create_app()
    cors = CORS(app, allow_headers=('Content-Type', 'Authorization', 'X-BB-Api-Client-Version'))
    app.run('0.0.0.0', port=5000, debug=True)
