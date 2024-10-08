from datetime import timedelta
from airflow.decorators import dag

import dlt
from dlt.common import pendulum
from airflow.operators.empty import EmptyOperator
from dlt.sources.credentials import ConnectionStringCredentials

from astroingest.dlt_pipeline_task_group import DltPipelineTaskGroup

default_task_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": "test@test.com",
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "execution_timeout": timedelta(hours=20),
}


@dag(
    schedule_interval="@daily",
    start_date=pendulum.datetime(2023, 7, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_task_args,
)
def astroingest_load_data():
    """
    Same as the dag_rest_api_pokemon DAG, but written with DltPipelineTaskGroup to abstract the dlt pipeline creation.
    """
    from include.rest_api import pokemon_source as api_source
    from include.sql_database import sql_database

    mysql_source = sql_database(
        ConnectionStringCredentials(
            "mysql://airflow:mysql_password@mysql:3306/airflow"
        ),
        "airflow",
    )
    postgres_destination = dlt.destinations.postgres(
        "postgres://airflow:pg_password@postgres:5432/airflow"
    )

    pre_dlt = EmptyOperator(task_id="pre_dlt")

    dlt_task_group_api_pg = DltPipelineTaskGroup(
        pipeline_name="astroingest_api_postgres_pipeline",
        dlt_source=api_source(),
        dataset_name="pokemon",
        destination=postgres_destination,
        use_data_folder=False,
        wipe_local_data=True,
    )

    dlt_task_group_mysql_pg = DltPipelineTaskGroup(
        pipeline_name="astroingest_mysql_postgres_pipeline",
        dlt_source=mysql_source,
        dataset_name="mysql_source",
        destination=postgres_destination,
        use_data_folder=False,
        wipe_local_data=True,
    )

    post_dlt = EmptyOperator(task_id="post_dlt")

    (pre_dlt >> dlt_task_group_api_pg >> dlt_task_group_mysql_pg >> post_dlt)


astroingest_load_data()
