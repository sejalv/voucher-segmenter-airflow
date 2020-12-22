import os
import pyarrow.parquet as pq
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine

# TODO: scope to optimize code, break into different jobs/utils


s3_conn_id = 'my_s3_conn_id'
s3_path = os.environ.get('S3_PATH')
pg_user = os.environ.get('POSTGRES_USER')
pg_password = os.environ.get('POSTGRES_PASSWORD')
pg_db = os.environ.get('POSTGRES_DB')
pg_host = os.environ.get('POSTGRES_HOST')
pg_port = os.environ.get('POSTGRES_PORT')


def prepare_vouchers_Peru():

    conn = create_engine('postgresql://{}:{}@{}:{}/{}'.format(pg_user, pg_password, pg_host, pg_port, pg_db))

    # fetch data from customer_segments (job: load_pg_customer_segments)
    df_segments = psql.read_sql("select * from voucher_customer.customer_segments", conn)
    df_segments_recency = df_segments[df_segments['segment_name'] == 'recency_segment']
    df_segments_frequent = df_segments[df_segments['segment_name'] == 'frequent_segment']

    # fetch voucher data from S3 parquet
    df = pd.read_parquet(s3_path, engine='pyarrow')
    df.reset_index(level=0, inplace=True)

    # cleanse
    df_Peru = df[df['country_code'] == 'Peru']
    df_Peru['voucher_amount'] = df_Peru['voucher_amount'].fillna(0)
    df_Peru['total_orders'] = pd.to_numeric(df_Peru['total_orders']).fillna(0)
    df_Peru['last_order_ts'] = pd.to_datetime(df_Peru['last_order_ts'])
    df_Peru['first_order_ts'] = pd.to_datetime(df_Peru['first_order_ts'])
    df_Peru['days_since_last_order'] = (pd.Timestamp.utcnow() - df_Peru['last_order_ts']).dt.days

    # map to recency segments
    df_segments_recency.index = pd.IntervalIndex.from_arrays(
        df_segments_recency['min_range'], df_segments_recency['max_range'], closed='both'
    )
    df_Peru['segment_type'] = df_Peru['days_since_last_order'].apply(
        lambda x: df_segments_recency.iloc[df_segments_recency.index.get_loc(x)]['segment_type']
    )
    df_Peru_recency = pd.merge(
        df_Peru, df_segments_recency, how='inner', left_on='segment_type', right_on='segment_type'
    )
    df_Peru.drop(columns=['segment_type'], inplace=True)

    # map to frequent segments
    df_segments_frequent.index = pd.IntervalIndex.from_arrays(
        df_segments_frequent['min_range'], df_segments_frequent['max_range'], closed='both'
    )
    df_Peru['segment_type'] = df_Peru['total_orders'].apply(
        lambda x: df_segments_frequent.iloc[df_segments_frequent.index.get_loc(x)]['segment_type']
    )
    df_Peru_frequent = pd.merge(
        df_Peru, df_segments_frequent, how='inner', left_on='segment_type', right_on='segment_type'
    )
    df_Peru.drop(columns=['segment_type'], inplace=True)

    df_Peru_recency_grouped = df_Peru_recency.groupby(
        ['min_range', 'max_range', 'segment_name', 'voucher_amount']).size().to_frame('count').reset_index()

    df_Peru_frequent_grouped = df_Peru_frequent.groupby(
        ['min_range', 'max_range', 'segment_name', 'voucher_amount']).size().to_frame('count').reset_index()

    df_Peru_grouped = df_Peru_recency_grouped.append(df_Peru_frequent_grouped)

    # save to postgres
    df_Peru_grouped.to_sql(name='voucher_segments', con=conn, schema='voucher_customer', if_exists='replace')

    #################################################

    # extra:
    df_Peru_recency.rename(columns={
        "segment_type": "recency_segment_type", "min_range": "recency_min",
        "max_range": "recency_max", "segment_name": "recency_segment"
    }, inplace=True)

    df_Peru_frequent.rename(columns={
        "segment_type": "frequent_segment_type", "min_range": "frequent_min",
        "max_range": "frequent_max", "segment_name": "frequent_segment"
    }, inplace=True)

    df_Peru = pd.merge(
        df_Peru_recency, df_Peru_frequent, how='inner',
        left_on=['index', 'timestamp', 'country_code', 'last_order_ts', 'first_order_ts', 'total_orders', 'voucher_amount', 'days_since_last_order'],
        right_on=['index', 'timestamp', 'country_code', 'last_order_ts', 'first_order_ts', 'total_orders', 'voucher_amount', 'days_since_last_order']
    )

    df_Peru.to_sql(name='voucher_selector', con=conn, schema='voucher_customer', if_exists='replace')
