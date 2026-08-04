from __future__ import annotations

import logging

from pyspark.sql import DataFrame

logger = logging.getLogger(__name__)


def write_gold_view(df: DataFrame, table_path: str) -> int:
    """Materializza una vista Gold come tabella Delta (overwrite).

    A differenza di Bronze (append-only) e Silver (upsert), le viste Gold
    sono sempre ricalcolate da zero ad ogni esecuzione: sono aggregazioni
    derivate, non hanno bisogno di storicizzazione propria — la storia
    vive già in Bronze, e queste tabelle sono solo una "fotografia" pronta
    da servire velocemente alla dashboard (Fase 8) senza ricalcolare le
    aggregazioni ad ogni refresh.
    """
    count = df.count()
    df.write.format("delta").mode("overwrite").save(table_path)
    logger.info("vista Gold scritta: path=%s righe=%d", table_path, count)
    return count
