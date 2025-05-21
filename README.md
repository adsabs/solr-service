
[![Coverage Status](https://coveralls.io/repos/adsabs/solr-service/badge.svg?branch=master&service=github)](https://coveralls.io/github/adsabs/solr-service?branch=master)

# Microservice responsible for proxying requests to Solr

This service is a part of the ADS API. It is a tiny proxy in front of the SOLR.

## Development/Installation

> [!IMPORTANT]  
> To avoid installation headaches it's strongly suggested [that you use `uv`](https://docs.astral.sh/uv/), a fast and flexible alternative to `pip`. We still have some Python infrastructure that runs on Python 2, which can cause package installation errors that are difficult to resolve without excluding newer package versions.

If you wish to install the service locally:

  1. create a python virtual environment using uv: `uv venv -p 3.9 venv/`
  2. activate the new virtual environment: `source venv/bin/activate` (or its Windows equivalent)
  3. install dependencies, excluding newer versions of `setuptools` that break the installation:

```
uv pip install --exclude-newer='2022-01-01' -r requirements.txt && uv pip install --exclude-newer='2022-01-01' -r dev-requirements.txt
```
If you get an error like: error in ConcurrentLogHandler setup command: use_2to3 is invalid.
try downgrading your setuptools package. Note, you also need to install wheel in the venv.
```
uv pip uninstall setuptools
uv pip install setuptools==57.5.0 wheel
```
  4. create a `solr/local_config.py` and point at your SOLR instances, one for queries that do not require the citation graph cache and one for second order queries. example:

```
SOLR_SERVICE_URL='http://localhost:8983/solr'
SECOND_ORDER_SOLR_SERVICE_URL='http://localhost:8983/solr'
```
NB: these can be the same server. Note also, they actually should point to a collection name for local testing.

  5. start the solr-service `python cors.py`


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
