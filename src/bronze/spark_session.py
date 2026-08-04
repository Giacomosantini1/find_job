from __future__ import annotations

import os

from pyspark.sql import SparkSession


def get_spark_session(app_name: str = "job-intel-bronze") -> SparkSession:
    """Crea una SparkSession con supporto Delta Lake.

    Su Databricks la sessione `spark` è già fornita dal runtime con Delta
    nativo: in quel caso basta usare `SparkSession.builder.getOrCreate()`.
    Questa funzione gestisce anche l'esecuzione locale/CI, dove Delta va
    configurato esplicitamente tramite `delta-spark`.
    """
    if os.environ.get("DATABRICKS_RUNTIME_VERSION"):
        return SparkSession.builder.appName(app_name).getOrCreate()

    from delta import configure_spark_with_delta_pip

    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()
