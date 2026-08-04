from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def compute_active_companies(spark: SparkSession, silver_path: str) -> DataFrame:
    """Classifica le aziende per numero di offerte aperte attualmente in Silver.

    Silver rappresenta lo stato corrente (Fase 3), quindi questo conteggio
    riflette le posizioni aperte *ora*, non un cumulato storico. Per un
    trend nel tempo (es. "aziende che assumono di più questo mese")
    servirebbe invece appoggiarsi allo storico Bronze, stessa logica già
    usata in `new_removed_postings.py`.
    """
    df = spark.read.format("delta").load(silver_path)

    return (
        df.groupBy("company")
        .agg(
            F.count("*").alias("open_postings_count"),
            F.countDistinct("source").alias("distinct_sources"),
        )
        .orderBy(F.col("open_postings_count").desc())
    )
