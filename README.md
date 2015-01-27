
[![Build Status](https://travis-ci.org/adsabs/solr-service.svg?branch=master)](https://travis-ci.org/adsabs/solr-service)

# Microservice responsible for proxying requests to Solr

To request bigquery data:

```python
requests.post('http://localhost:5000/bigquery', params={'q':'*:*', 'wt':'json', 'fl':'bibcode', 'fq': '{!bitset}'}, data='bibcode\n1907AN....174...59.\n1908PA.....16..445.\n1989LNP...334..242S')
```

