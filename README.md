
[![Coverage Status](https://coveralls.io/repos/adsabs/solr-service/badge.svg?branch=master&service=github)](https://coveralls.io/github/adsabs/solr-service?branch=master)

# Microservice responsible for proxying requests to Solr

This service is a part of the ADS API. It is a tiny proxy in front of the SOLR.

## Development/Installation

If you wish to install the service locally:

  1. create a python virtual environment `virtualenv python`
  1. install dependencies `pip install -r requirements.txt; pip install -r dev-requirements.txt`
  1. create a `solr/local_config.py` and point at your SOLR instance, example:

```
SOLR_SERVICE_URL='http://localhost:8983/solr'
```
  1. start the solr-service `python cors.py`


Note: normally, we run the `solr-service` using gunicorn (wsgi.py) behind the `adsws` gateway.
In this case, we use `cors.py` to run the `solr-service` as a standalone service (without needing
the ADS gateway).

## Specifying Limits

Additional facets can be made available to users by specifying them in the `Limits` table. The table takes one `facet` along with an associated filter per user per line.
these entries are currently inserted manually
```sql
INSERT INTO public.limits (uid, field, filter)
VALUES (user_id, solr_field, filter);
```
filter can be `*:*`.

## End User Api Documentation

The API documentation is available at: https://github.com/adsabs/adsabs.github.io/blob/new-api/content/v1/search.md
