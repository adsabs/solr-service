
from flask_cors import CORS
from solr.app import create_app

if __name__ == '__main__':
    app = create_app()
    app.logger_name = "solr-service"
    cors = CORS(app, allow_headers=('Content-Type', 'Accept', 'Credentials', 'Authorization', 'X-BB-Api-Client-Version'), supports_credentials=True, origins=['http://localhost:8000'])
    app.run('0.0.0.0', port=5000, debug=True)
