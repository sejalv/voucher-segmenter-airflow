## Voucher Segmenter Airflow

### Overview

A pipeline & API for voucher selection built with Airflow, Postgres, Flask, and Docker

The task is to create a Voucher Selection API for the country: Peru
There are 3 steps that should be done:
0. Conduct data analysis to explore and prepare the data.
1. Create a data pipeline to generate customer segments, including data cleaning, optimization.
2. Create a REST API that will expose the most used voucher value for a particular customer
segment.

This is a sandbox project to set up an environment with Airflow and Docker in order to schedule and monitor pipelines.

## Structure

### Containers

`docker-compose` is used to launch:
* `postgres` or voucher-segmenter-airflow_postgres_1:  Postgres Database instance
* `airflow` or voucher-segmenter-airflow_webserver_1: `LocalExecutor` Airflow setup
* `api` or voucher-segmenter-airflow_api_1: Local API using Flask

### Database
* Version: postgres:9.6
* Schema: `voucher_customer`
* Config: `docker-compose.yml`

### Data pipeline:

Version: Airflow v1.10.9, with Python 3.7 (using [puckel/docker-airflow](https://github.com/puckel/docker-airflow))
Config: `dags` dir, root dir files

#### Process

1. Generates `voucher_customer.customer_segments` table by loading data from `customer_segments.sql`
2. Fetches voucher data from the S3 parquet
3. Cleanses, filters, and maps the voucher data to customer segments.
4. Updates the `voucher_customer.voucher_segments` table daily, with the count of vouchers used for a particular segment_type

#### Final Output
```
$ docker-compose exec postgres psql -U airflow
psql (9.6.20)
Type "help" for help.

airflow=# select * from voucher_customer.voucher_segments;
 index | min_range | max_range |   segment_name   | voucher_amount | count 
-------+-----------+-----------+------------------+----------------+-------
     0 |       180 |  99999999 | recency_segment  |              0 | 13950
     1 |       180 |  99999999 | recency_segment  |           2640 | 49102
     2 |       180 |  99999999 | recency_segment  |           3520 | 22037
     3 |       180 |  99999999 | recency_segment  |           4400 | 21458
     0 |         0 |         4 | frequent_segment |              0 |  4543
     1 |         0 |         4 | frequent_segment |           2640 | 16496
     2 |         0 |         4 | frequent_segment |           3520 |  7758
     3 |         0 |         4 | frequent_segment |           4400 |  7402
     4 |         5 |        13 | frequent_segment |              0 |   253
     5 |         5 |        13 | frequent_segment |           2640 |  4112
     6 |         5 |        13 | frequent_segment |           3520 |  1374
     7 |         5 |        13 | frequent_segment |           4400 |  1272
     8 |        14 |        37 | frequent_segment |              0 |  1501
     9 |        14 |        37 | frequent_segment |           2640 | 11813
    10 |        14 |        37 | frequent_segment |           3520 |  4391
    11 |        14 |        37 | frequent_segment |           4400 |  4225
    12 |        38 |  99999999 | frequent_segment |              0 |  7653
    13 |        38 |  99999999 | frequent_segment |           2640 | 16681
    14 |        38 |  99999999 | frequent_segment |           3520 |  8514
    15 |        38 |  99999999 | frequent_segment |           4400 |  8559
(20 rows)

```

### API

The Flask API (http://localhost:5000) which queries from `voucher_customer.voucher_segments`
Config: `api` dir, `docker-compose.yml`

## Setup

### Prerequisites
To run this locally, you would need a few things:
* Docker installed
* S3 bucket and access details (`Dockerfile`, `.env`)

### Clone respository
```
$ git clone https://github.com/sejalv/voucher-segmenter-airflow.git
```

### Move into new directory
```
$ cd voucher-segmenter-airflow
```

### Generate a fernet key for your environment and pipe into env file
```
$ echo $(echo "FERNET_KEY='")$(openssl rand -base64 32)$(echo "'") >> airflow.env
```

## Execution

### Launch docker containers in detached session
```
$ docker-compose up --build
```

### In a new tab, initialise database for webserver
```
$ docker-compose exec webserver airflow initdb
```

### Trigger pipeline
#### Trigger from command line
```
$ docker-compose exec webserver airflow trigger_dag voucher_segmenter
```
#### Or trigger from web UI
* Open browser to `http://127.0.0.1:8080/`

### Call API
```
$ curl -X GET -H "Content-type: application/json" -d '{"customer_id": 123, "country_code": "Peru", "last_order_ts": "2018-05-03 00:00:00", "first_order_ts": "2017-05-03 00:00:00", "total_orders": 15, "segment_name": "recency_segment"}' "http://localhost:5000/voucher_amount"

{"voucher_amount":[2640.0]}
```

## Test

(TBD: Config error)
```
$ docker-compose exec webserver python -m unittest -v
```

## End
### Close docker session
```
$ docker-compose down
```

### Caveats

* you may need to check your `FERNET_KEY`
* you may need to manually update `postgres_default` on the Airflow console
(http://127.0.0.1:8080/admin/connection/)

## Future Enhancements
* Airflow tasks run on same machine as scheduler
* Parallelisation of tasks (workers) possible, use of CeleryExecutor
* Breaking down of utility functions into tasks for the pipeline, in `prepare_data.py`
* ORM and security in Flask API
