from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType

from .extractor import extract_technologies

# UDF registrata una sola volta a livello di modulo: Spark serializza questa
# funzione per ogni executor, quindi va tenuta leggera (extract_technologies
# è puro Python, nessuna dipendenza pesante da serializzare).
_extract_technologies_udf = F.udf(extract_technologies, ArrayType(StringType()))


def enrich_with_technologies(silver_df: DataFrame) -> DataFrame:
    """Popola/aggiorna la colonna `technologies` a partire da `description`.

    Progettato per essere applicato al DataFrame Silver già normalizzato
    (dopo il mapping per fonte, prima della MERGE finale): in questo modo
    i mapper (Fase 3) restano responsabili solo della normalizzazione
    per-fonte, mentre l'estrazione skill è una responsabilità trasversale
    applicata uniformemente indipendentemente dalla fonte di origine.
    """
    return silver_df.withColumn(
        "technologies", _extract_technologies_udf(F.col("description"))
    )
