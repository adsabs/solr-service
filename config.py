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
SOLR_SERVICE_DEFAULT_FIELDS = ['id', 'recid', 'title', 'abstract', 'author', 'bibcode', 'identifier', 'volume', 'page', 'bibstem', 'doctype', 'pubdate', 'pub', 'pub_raw', 'citation_count', 'read_count', 'esources']
SOLR_SERVICE_DISALLOWED_FIELDS = ['body', 'full', 'ack', 'readers', 'reader', 'email']
SOLR_SERVICE_ALLOWED_FACET_FIELDS = ['bibstem_facet', 'author_facet_hier', 'property', 'keyword_facet', 'year', 'bibgroup_facet', 'data_facet', 'vizier_facet', 'grant_facet_hier', 'database', 'simbad_object_facet_hier', 'aff_facet_hier', 'doctype_facet_hier', 'first_author_facet_hier', 'ned_object_facet_hier',]
SOLR_SERVICE_ALLOWED_FACET_PIVOT = ['property', 'year', 'citation_count', 'read_count', 'year']
SOLR_SERVICE_ALLOWED_STATS_FIELDS = ['citation_count', 'read_count', 'citation_count_norm']
SOLR_SERVICE_ALLOWED_HIGHLIGHTS_FIELDS = ['title', 'abstract']
SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS = ['ieee']
SOLR_SERVICE_ALLOWED_SORT_FIELDS = ['id asc', 'author_count asc', 'bibcode asc', 'citation_count asc', 'citation_count_norm asc', 'classic_factor asc', 'first_author asc', 'date asc', 'entry_date asc', 'read_count asc', 'score asc', 'id desc', 'author_count desc', 'bibcode desc', 'citation_count desc', 'citation_count_norm desc', 'classic_factor desc', 'first_author desc', 'date desc', 'entry_date desc', 'read_count desc', 'score desc',]
#SOLR_SERVICE_TIME_ALLOWED_MS = 60000
SOLR_SERVICE_BOOST_TYPES = {'astrophysics': 'astronomy_final_boost', 'physics': 'physics_final_boost', 'earthscience': 'earth_science_final_boost', 'planetary': 'planetary_science_final_boost', 'heliophysics': 'heliophysics_final_boost', 'general': 'general_final_boost'}
SOLR_SERVICE_MAX_ROWS = 2000
SOLR_SERVICE_DEFAULT_ROWS = 10
SOLR_INJECT_QUERY_PARAMS = dict()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = "sqlite:///"
SOLR_SERVICE_ALLOWED_FIELDS = [
    'abstract', 'ack', 'aff', 'alternate_bibcode', 'alternate_title',
    'arxiv_class', 'author', 'bibcode', 'bibgroup', 'bibstem',
    'citation_count', 'copyright', 'data', 'database', 'doctype', 'doi',
    'first_author', 'grant', 'has', 'id', 'identifier', 'indexstamp', 'issue',
    'keyword', 'lang', 'orcid_other', 'orcid_pub', 'orcid_user', 'page',
    'property', 'pub', 'pubdate', 'read_count', 'title', 'vizier', 'volume',
    'year'
]
BOT_SOLR_SERVICE_URL = os.environ.get('BOT_SOLR_SERVICE_URL', SOLR_SERVICE_URL)
BOT_SOLR_SERVICE_SEARCH_HANDLER = BOT_SOLR_SERVICE_URL + '/select'
BOT_SOLR_SERVICE_BIGQUERY_HANDLER = BOT_SOLR_SERVICE_URL + '/bigquery'
BOT_TOKENS = []
AFFINITY_ENHANCED_ENDPOINTS = {"/search": "sroute",} # keys: deploy paths, value: cookie
SQLALCHEMY_BINDS = {'solr_service': "sqlite:///"}
SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = None
SQLALCHEMY_MAX_OVERFLOW = None
SQLALCHEMY_RECORD_QUERIES = False
API_URL = 'http://adsws'
VAULT_ENDPOINT = API_URL + '/vault/query'
LIBRARY_ENDPOINT = API_URL + '/biblib/libraries'
