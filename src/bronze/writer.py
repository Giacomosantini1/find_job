from __future__ import annotations

import json
import logging
from datetime import date

from pyspark.sql import DataFrame, SparkSession

from src.ingestion.models import RawJobPosting

from .schema import BRONZE_JOB_POSTINGS_SCHEMA

logger = logging.getLogger(__name__)


class BronzeWriter:
    """Scrive le offerte grezze in una tabella Delta, in modalità append-only.

    Bronze è lo storico immutabile: ogni esecuzione aggiunge un nuovo batch,
    anche se un'offerta era già presente in un batch precedente. La
    deduplicazione/merge verso lo "stato corrente" avviene nel Silver layer
    (Fase 3); questa scelta permette al Gold layer di calcolare "offerte
    nuove/rimosse" confrontando batch consecutivi.
    """

    def __init__(self, spark: SparkSession, table_path: str) -> None:
        self.spark = spark
        self.table_path = table_path

    def _to_dataframe(
        self, postings: list[RawJobPosting], ingestion_date: date
    ) -> DataFrame:
        rows = [
            (
                p.source,
                p.source_job_id,
                p.company_identifier,
                p.fetched_at,
                p.url,
                json.dumps(p.raw_payload, ensure_ascii=False),
                ingestion_date,
            )
            for p in postings
        ]
        return self.spark.createDataFrame(rows, schema=BRONZE_JOB_POSTINGS_SCHEMA)

    def write(
        self, postings: list[RawJobPosting], ingestion_date: date | None = None
    ) -> int:
        if not postings:
            logger.info("nessuna offerta da scrivere, skip")
            return 0

        run_date = ingestion_date or date.today()
        df = self._to_dataframe(postings, run_date).cache()
        row_count = df.count()

        (
            df.write.format("delta")
            .mode("append")
            .partitionBy("source", "ingestion_date")
            .save(self.table_path)
        )

        df.unpersist()
        logger.info(
            "scritte %d righe in Bronze (path=%s, ingestion_date=%s)",
            row_count, self.table_path, run_date,
        )
        return row_count
