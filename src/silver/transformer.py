from __future__ import annotations

import json
import logging

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from src.skills.enrich import enrich_with_technologies

from .mappers.registry import get_mapper
from .schema import SILVER_JOB_POSTINGS_SCHEMA

logger = logging.getLogger(__name__)

_SCHEMA_FIELD_ORDER = [f.name for f in SILVER_JOB_POSTINGS_SCHEMA.fields]


def _map_bronze_row(row: Row) -> Row:
    mapper = get_mapper(row["source"])
    raw_payload = json.loads(row["raw_payload"])
    record = mapper.map(
        raw_payload=raw_payload,
        company_identifier=row["company_identifier"],
        source_job_id=row["source_job_id"],
        url=row["url"],
    )
    values = {field: record[field] for field in _SCHEMA_FIELD_ORDER}  # type: ignore[literal-required]
    return Row(**values)


class SilverTransformer:
    def __init__(self, spark: SparkSession, bronze_path: str, silver_path: str) -> None:
        self.spark = spark
        self.bronze_path = bronze_path
        self.silver_path = silver_path

    def _read_latest_per_job_id(self, bronze_df: DataFrame) -> DataFrame:
        mapped_rdd = bronze_df.rdd.map(_map_bronze_row)
        mapped_df = self.spark.createDataFrame(mapped_rdd, schema=SILVER_JOB_POSTINGS_SCHEMA)

        window = Window.partitionBy("job_id").orderBy(F.col("publication_date").desc_nulls_last())
        deduplicated = (
            mapped_df.withColumn("_rank", F.row_number().over(window))
            .filter(F.col("_rank") == 1)
            .drop("_rank")
        )
        # Skill Extraction (Fase 5): popola `technologies` a partire dalla
        # `description` normalizzata, indipendentemente dalla fonte.
        return enrich_with_technologies(deduplicated)

    def transform(self) -> int:
        bronze_df = self.spark.read.format("delta").load(self.bronze_path)
        silver_batch = self._read_latest_per_job_id(bronze_df).cache()
        batch_count = silver_batch.count()

        if batch_count == 0:
            logger.info("nessuna riga da normalizzare, skip")
            return 0

        if DeltaTable.isDeltaTable(self.spark, self.silver_path):
            target = DeltaTable.forPath(self.spark, self.silver_path)
            (
                target.alias("target")
                .merge(silver_batch.alias("source"), "target.job_id = source.job_id")
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
            logger.info("merge completato: %d righe processate", batch_count)
        else:
            silver_batch.write.format("delta").mode("overwrite").save(self.silver_path)
            logger.info("tabella Silver creata con %d righe", batch_count)

        silver_batch.unpersist()
        return batch_count
