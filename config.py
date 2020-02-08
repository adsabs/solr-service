import os

LOG_LEVEL = 30 # To be deprecated when all microservices use ADSFlask
LOGGING_LEVEL = "INFO"
LOG_STDOUT = True
SOLR_SERVICE_VERSION = 'v4.10'
SOLR_SERVICE_URL = os.environ.get('SOLR_SERVICE_URL', 'http://localhost:8983/solr')
SOLR_SERVICE_TVRH_HANDLER = SOLR_SERVICE_URL + '/tvrh'
SOLR_SERVICE_SEARCH_HANDLER = SOLR_SERVICE_URL + '/select'
SOLR_SERVICE_QTREE_HANDLER = SOLR_SERVICE_URL + '/qtree'
SOLR_SERVICE_BIGQUERY_HANDLER = SOLR_SERVICE_URL + '/bigquery'
SOLR_SERVICE_FORWARDED_COOKIES = set(['sroute'])
SOLR_SERVICE_DISALLOWED_FIELDS = ['body', 'full', 'reader']
SOLR_SERVICE_ALLOWED_FACET_FIELDS = ['bibstem_facet', 'author_facet_hier', 'property', 'keyword_facet', 'year', 'bibgroup_facet', 'data_facet', 'vizier_facet', 'grant_facet_hier', 'database', 'simbad_object_facet_hier', 'aff_facet_hier', 'doctype_facet_hier', 'first_author_facet_hier', 'ned_object_facet_hier',]
SOLR_SERVICE_MAX_ROWS = 2000
SOLR_SERVICE_DEFAULT_ROWS = 10
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = "sqlite:///"
SOLR_SERVICE_ALLOWED_FIELDS = [
    'abstract', 'ack', 'aff', 'alternate_bibcode', 'alternate_title',
    'arxiv_class', 'author', 'bibcode', 'bibgroup', 'bibstem',
    'citation_count', 'copyright', 'data', 'database', 'doctype', 'doi',
    'first_author', 'grant', 'id', 'identifier', 'indexstamp', 'issue',
    'keyword', 'lang', 'orcid_other', 'orcid_pub', 'orcid_user', 'page',
    'property', 'pub', 'pubdate', 'read_count', 'title', 'vizier', 'volume',
    'year'
]
BOT_SOLR_SERVICE_URL = os.environ.get('BOT_SOLR_SERVICE_URL', SOLR_SERVICE_URL)
BOT_SOLR_SERVICE_SEARCH_HANDLER = BOT_SOLR_SERVICE_URL + '/select'
BOT_SOLR_SERVICE_BIGQUERY_HANDLER = BOT_SOLR_SERVICE_URL + '/bigquery'
BOT_TOKENS = []

API_URL = 'http://adsws'
VAULT_ENDPOINT = API_URL + '/vault/query'
LIBRARY_ENDPOINT = API_URL + '/biblib/libraries'
