APP_SECRET_KEY = 'fake'
VERSION = 'v4.10' # Arbitrary string identifying solr (will be returned in the headers)

SOLR_URL = 'http://localhost:8983/solr'

SOLR_TVRH_HANDLER = SOLR_URL + '/tvrh'
SOLR_SEARCH_HANDLER = SOLR_URL + '/select'
SOLR_QTREE_HANDLER = SOLR_URL + '/qtree'
SOLR_BIGQUERY_HANDLER = SOLR_URL + '/bigquery'

