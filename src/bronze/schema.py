from __future__ import annotations

from pyspark.sql.types import (
    DateType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# Schema esplicito della tabella Bronze: nessuna inferenza automatica.
# raw_payload resta stringa JSON (non parsata): la struttura varia per fonte
# e la normalizzazione è compito del Silver layer, non del Bronze.
BRONZE_JOB_POSTINGS_SCHEMA = StructType(
    [
        StructField("source", StringType(), nullable=False),
        StructField("source_job_id", StringType(), nullable=False),
        StructField("company_identifier", StringType(), nullable=False),
        StructField("fetched_at", TimestampType(), nullable=False),
        StructField("url", StringType(), nullable=True),
        StructField("raw_payload", StringType(), nullable=False),
        StructField("ingestion_date", DateType(), nullable=False),
    ]
)
