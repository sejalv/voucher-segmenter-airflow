from flask import Flask, request, jsonify
from datetime import datetime
from logger import logger
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import psycopg2
import time
import os

pg_user = os.environ.get('POSTGRES_USER')
pg_password = os.environ.get('POSTGRES_PASSWORD')
pg_db = os.environ.get('POSTGRES_DB')
pg_host = os.environ.get('POSTGRES_HOST')
pg_port = os.environ.get('POSTGRES_PORT')
conn_pg = 'postgresql://{}:{}@{}:{}/{}'.format(pg_user, pg_password, pg_host, pg_port, pg_db)

while 1:
    try:
        e = sqlalchemy.create_engine(conn_pg)
        e.execute('select 1')
    except Exception as OperationalError:
        print('Waiting for database...')
        time.sleep(1)
    else:
        break
print('Connected!')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = conn_pg
db = SQLAlchemy(app)
session = db.session()

@app.route('/')
def health():
    return 'OK'


@app.route('/voucher_amount')
def get_voucher_amount():
    try:

        obj = request.get_json()
        if obj['segment_name'] == 'recency_segment':
            td = datetime.today() - datetime.strptime(obj['last_order_ts'], '%Y-%m-%d %H:%M:%S')
            query = f'''
                select voucher_amount
                from voucher_customer.voucher_segments 
                where count = (
                select max(count)
                from voucher_customer.voucher_segments 
                where segment_name = '{obj['segment_name']}' 
                and {td.days} between min_range and max_range) 
                and segment_name = '{obj['segment_name']}'
            '''
        else:
            query = f'''
                select voucher_amount
                from voucher_customer.voucher_segments 
                where count = (
                select max(count)
                from voucher_customer.voucher_segments 
                where segment_name = '{obj['segment_name']}' 
                and {obj['total_orders']} between min_range and max_range) 
                and segment_name = '{obj['segment_name']}'
            '''

        mycursor = session.execute(query).cursor
        voucher_amount = mycursor.fetchone()
        return jsonify({'voucher_amount': voucher_amount})

    except Exception as e:
        logger.error(e)
        return 'API Error'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
