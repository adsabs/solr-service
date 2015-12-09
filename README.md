
[![Build Status](https://travis-ci.org/adsabs/solr-service.svg?branch=master)](https://travis-ci.org/adsabs/solr-service)
[![Coverage Status](https://coveralls.io/repos/adsabs/solr-service/badge.svg?branch=master&service=github)](https://coveralls.io/github/adsabs/solr-service?branch=master)

# Microservice responsible for proxying requests to Solr

To request bigquery data:

```python
requests.post('http://localhost:5000/bigquery', params={'q':'*:*', 'wt':'json', 'fl':'bibcode', 'fq': '{!bitset}'}, data='bibcode\n1907AN....174...59.\n1908PA.....16..445.\n1989LNP...334..242S')
```

