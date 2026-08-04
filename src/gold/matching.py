from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from src.matching.cv_profile import CVProfile
from src.matching.scorer import compute_match

_MATCH_RESULT_SCHEMA = StructType(
    [
        StructField("score", IntegerType()),
        StructField("matched_skills", ArrayType(StringType())),
        StructField("missing_skills", ArrayType(StringType())),
        StructField("matched_keywords", ArrayType(StringType())),
        StructField("required_years", DoubleType()),
        StructField("rationale", StringType()),
    ]
)


def compute_match_scores(
    spark: SparkSession, silver_path: str, cv_profile: CVProfile
) -> DataFrame:
    """Applica il Matching Engine a tutte le offerte in Silver.

    `cv_profile` viene catturato per closure nella UDF: essendo un
    `dataclass` immutabile composto solo da tipi Python nativi (frozenset
    di stringhe, float), Spark lo serializza correttamente verso gli
    executor senza richiedere configurazione aggiuntiva.
    """
    silver_df = spark.read.format("delta").load(silver_path)

    def _match_row(job_id: str, technologies: list[str] | None, description: str | None):
        result = compute_match(cv_profile, job_id, technologies, description)
        return (
            result.score,
            result.matched_skills,
            result.missing_skills,
            result.matched_keywords,
            result.required_years,
            result.rationale,
        )

    match_udf = F.udf(_match_row, _MATCH_RESULT_SCHEMA)

    enriched = silver_df.withColumn(
        "match", match_udf(F.col("job_id"), F.col("technologies"), F.col("description"))
    )

    return enriched.select(
        "job_id",
        "company",
        "title",
        "location",
        "remote",
        "link",
        F.col("match.score").alias("match_score"),
        F.col("match.matched_skills").alias("matched_skills"),
        F.col("match.missing_skills").alias("missing_skills"),
        F.col("match.matched_keywords").alias("matched_keywords"),
        F.col("match.required_years").alias("required_years"),
        F.col("match.rationale").alias("rationale"),
    ).orderBy(F.col("match_score").desc())
