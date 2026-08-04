from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def compute_duplicate_postings(spark: SparkSession, silver_path: str) -> DataFrame:
    """Rileva offerte duplicate tra fonti diverse per la stessa azienda.

    Definizione di duplicato usata in questa fase: stessa `company` e
    stesso `title` normalizzato (case/spazi ignorati), pubblicati da fonti
    differenti (`source`). È una regola volutamente semplice ed esplicita
    per iniziare: un'azienda spesso pubblica la stessa posizione sia sul
    proprio ATS Greenhouse sia su SmartRecruiters in parallelo.

    Non usiamo qui similarità testuale/embedding sulla `description`,
    perché introdurrebbe un costo computazionale e una soglia arbitraria
    di similarità non giustificabile senza dati reali di validazione: la
    priorità è partire da una regola trasparente e verificabile, poi
    eventualmente affinarla con l'NLP quando emergono falsi positivi/negativi
    concreti.
    """
    df = spark.read.format("delta").load(silver_path)

    normalized = df.withColumn(
        "_title_key", F.lower(F.trim(F.regexp_replace(F.col("title"), r"\s+", " ")))
    )

    window = Window.partitionBy("company", "_title_key")
    grouped = normalized.withColumn("duplicate_count", F.count("*").over(window))

    return (
        grouped.filter(F.col("duplicate_count") > 1)
        .select(
            "job_id", "company", "title", "source", "link", "duplicate_count"
        )
        .orderBy("company", "title")
    )
