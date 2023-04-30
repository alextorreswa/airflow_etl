''' Basic ETL DAG'''
from datetime import datetime, date
import pandas as pd
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow import DAG

with DAG(
    dag_id='basic_etl_dag',
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False) as dag:

    extract_task = BashOperator(
        task_id='extract_task',
        bash_command='wget -c https://datahub.io/core/s-and-p-500-companies/r/constituents.csv -O /workspaces/airflow_etl/data/exract_sp500.csv'
        )

    def transform_data():
        """Read in the file, and write a transformed file out"""
        today = date.today()
        df = pd.read_csv('/workspaces/airflow_etl/data/exract_sp500.csv')
        group_series = df.groupby(['Sector'])['Sector'].count()
        group_df = pd.DataFrame(group_series)
        group_df.columns = ['Count']
        group_df['Date'] = today.strftime('%Y-%m-%d')
        group_df = group_df.reset_index()
        group_df.to_csv('/workspaces/airflow_etl/data/transform_sp500.csv', index=False)

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform_data,
        dag=dag)

    load_task = BashOperator(
        task_id='load_task',
        bash_command='echo -e ".separator ","\n.import --skip 1 /workspaces/airflow_etl/data/transform_sp500.csv sp_500_sector_count" | sqlite3 /workspaces/airflow_etl/data/sp_500.db',
        dag=dag)

    extract_task >> transform_task >> load_task

