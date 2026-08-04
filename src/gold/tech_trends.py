from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def compute_tech_trends(spark: SparkSession, silver_path: str) -> DataFrame:
    """Conteggio delle tecnologie richieste nelle offerte attive.

    STUB per la Fase 4: `technologies` in Silver è oggi sempre `None`,
    perché viene popolato dalla Fase 5 (Skill Extraction), che analizza
    `description` per estrarre le keyword tecniche. La logica di
    aggregazione qui sotto (`explode` + `groupBy` + conteggio) è già
    corretta e non richiederà modifiche quando la Fase 5 sarà completata:
    basterà che `technologies` smetta di essere vuoto perché questa vista
    inizi a produrre risultati reali.
    """
    df = spark.read.format("delta").load(silver_path)

    return (
        df.filter(F.col("technologies").isNotNull())
        .withColumn("technology", F.explode("technologies"))
        .groupBy("technology")
        .agg(F.count("*").alias("mentions_count"))
        .orderBy(F.col("mentions_count").desc())
    )
