"""Esempio di utilizzo del Matching Engine (Fase 6) con il CV reale.

Esegui questo script dopo aver popolato Silver (Fasi 1-5) per ottenere il
ranking delle offerte più affini al tuo profilo.

Uso:
    python run_matching_example.py <bronze_path> <silver_path>
"""
from __future__ import annotations

import sys

from src.bronze.spark_session import get_spark_session
from src.gold.matching import compute_match_scores
from src.matching.cv_profile import build_cv_profile

# Estratto sintetico dal CV reale (fonte: "Giacomo Santini - resume.pdf"),
# sufficiente per l'estrazione di tecnologie/keyword tramite lo stesso
# vocabolario usato per le offerte (Fase 5). In produzione questo testo
# andrebbe letto direttamente dal file CV (PDF/DOCX) tramite una funzione
# di estrazione testo dedicata.
CV_TEXT = """
Senior Data Engineer with 5+ years of experience delivering scalable data
platforms and ETL/ELT solutions on Azure. Design and build Azure Databricks
and Azure Data Factory pipelines processing millions of records from 20+
enterprise data sources. Optimize SQL Server and Apache Spark workloads.
Skilled in PySpark, SQL Server, Power BI, Git, Azure DevOps, incremental
loads, metadata-driven pipelines, Agile delivery and stakeholder management.
"""

YEARS_OF_EXPERIENCE = 5.0


def main() -> None:
    if len(sys.argv) != 3:
        print("Uso: python run_matching_example.py <bronze_path> <silver_path>")
        sys.exit(1)

    _, silver_path = sys.argv[1], sys.argv[2]

    spark = get_spark_session(app_name="matching-example")
    cv_profile = build_cv_profile(CV_TEXT, years_experience=YEARS_OF_EXPERIENCE)

    matches_df = compute_match_scores(spark, silver_path, cv_profile)
    matches_df.select(
        "job_id", "company", "title", "match_score", "matched_skills",
        "missing_skills", "rationale",
    ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
