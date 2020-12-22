from datetime import timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils import dates

from voucher_segmenter.prepare_data import prepare_vouchers_Peru

default_args = {
    'owner': 'sejalv',
    'depends_on_past': False,
    'start_date': dates.days_ago(1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG(
    dag_id='voucher_segmenter',
    default_args=default_args,
    description='Prepare voucher data based on customer segments',
    schedule_interval='0 0 * * *'
)

start_operator = DummyOperator(
    task_id='start_dag',
    dag=dag
)

load_pg_customer_segments = PostgresOperator(
    task_id='load_pg_customer_segments',
    sql='sql/customer_segments.sql',
    dag=dag
)

prepare_vouchers_Peru = PythonOperator(
    task_id='prepare_vouchers_Peru',
    schema='voucher_customer',
    table='voucher_selector',
    dag=dag,
    python_callable=prepare_vouchers_Peru
)

end_operator = DummyOperator(
    task_id='stop_dag',
    dag=dag
)

start_operator >> load_pg_customer_segments >> prepare_vouchers_Peru >> end_operator
