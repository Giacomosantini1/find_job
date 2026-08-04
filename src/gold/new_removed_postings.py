from __future__ import annotations

from datetime import date

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def _distinct_job_ids_for_date(spark: SparkSession, bronze_path: str, ingestion_date: date) -> DataFrame:
    """Job IDs univoci visti in un preciso batch di ingestion.

    `job_id` qui è ricostruito come `source:source_job_id`, per essere
    coerente con la chiave usata nello schema Silver (vedi
    `SourceMapper.build_job_id`), senza dover rifare il mapping completo:
    a questo livello ci interessa solo l'identità dell'offerta, non i
    suoi campi normalizzati.
    """
    df = spark.read.format("delta").load(bronze_path)
    return (
        df.filter(F.col("ingestion_date") == ingestion_date)
        .select(
            F.concat_ws(":", F.col("source"), F.col("source_job_id")).alias("job_id")
        )
        .distinct()
    )


def compute_new_postings(
    spark: SparkSession,
    bronze_path: str,
    previous_date: date,
    current_date: date,
) -> DataFrame:
    """Offerte presenti nel batch `current_date` ma assenti in `previous_date`.

    Richiede Bronze append-only (Fase 2): se Bronze facesse upsert, il
    batch precedente non sarebbe più interrogabile e questo confronto
    sarebbe impossibile.
    """
    current = _distinct_job_ids_for_date(spark, bronze_path, current_date)
    previous = _distinct_job_ids_for_date(spark, bronze_path, previous_date)
    return current.subtract(previous).withColumn(
        "detected_as_new_on", F.lit(current_date)
    )


def compute_removed_postings(
    spark: SparkSession,
    bronze_path: str,
    previous_date: date,
    current_date: date,
) -> DataFrame:
    """Offerte presenti nel batch `previous_date` ma sparite in `current_date`.

    Interpretazione: l'annuncio non è più stato ri-scaricato nell'ultimo
    giro di ingestion, quindi si presume rimosso dalla fonte originale.
    """
    current = _distinct_job_ids_for_date(spark, bronze_path, current_date)
    previous = _distinct_job_ids_for_date(spark, bronze_path, previous_date)
    return previous.subtract(current).withColumn(
        "detected_as_removed_on", F.lit(current_date)
    )
