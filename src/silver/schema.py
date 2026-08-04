from __future__ import annotations

from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# Schema canonico Silver: unico contratto verso Gold e verso il Matching
# engine (Fase 6), indipendente dalla fonte di origine.
#
# `Technologies` resta vuoto in questa fase: viene popolato dallo Skill
# Extraction layer (Fase 5), che lavora sulla `description` già normalizzata.
SILVER_JOB_POSTINGS_SCHEMA = StructType(
    [
        StructField("job_id", StringType(), nullable=False),
        StructField("company", StringType(), nullable=False),
        StructField("title", StringType(), nullable=False),
        StructField("location", StringType(), nullable=True),
        StructField("remote", BooleanType(), nullable=True),
        StructField("salary", StringType(), nullable=True),
        StructField("description", StringType(), nullable=True),
        StructField("technologies", ArrayType(StringType()), nullable=True),
        StructField("source", StringType(), nullable=False),
        StructField("publication_date", TimestampType(), nullable=True),
        StructField("link", StringType(), nullable=True),
    ]
)
