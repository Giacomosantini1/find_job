from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def compute_tech_trends(spark: SparkSession, silver_path: str) -> DataFrame:
    """Conteggio delle tecnologie richieste nelle offerte attive.

    Dalla Fase 5 (Skill Extraction) in poi, `technologies` in Silver è
    popolato automaticamente a partire dalla `description`, quindi questa
    vista produce risultati reali senza alcuna modifica rispetto allo stub
    della Fase 4.
    """
    df = spark.read.format("delta").load(silver_path)

    return (
        df.filter(F.col("technologies").isNotNull())
        .withColumn("technology", F.explode("technologies"))
        .groupBy("technology")
        .agg(F.count("*").alias("mentions_count"))
        .orderBy(F.col("mentions_count").desc())
    )
