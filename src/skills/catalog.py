from __future__ import annotations

# Catalogo delle tecnologie riconosciute, con le rispettive varianti di
# scrittura più comuni. La chiave è il nome canonico che finirà nel campo
# `technologies` di Silver; i valori sono i pattern testuali da cercare
# (case-insensitive, word-boundary), in ordine dal più specifico al meno
# specifico per evitare falsi positivi (es. "PySpark" va cercato prima di
# "Spark" per non perdere l'informazione più precisa quando serve, anche
# se in questa versione entrambi vengono comunque riportati).
#
# Aggiungere una tecnologia = aggiungere una riga qui. Nessun'altra parte
# del sistema richiede modifiche (stesso principio "config as data" già
# usato in `ingestion/config.py` e `silver/mappers/registry.py`).
TECHNOLOGY_CATALOG: dict[str, list[str]] = {
    "Spark": ["spark", "pyspark", "apache spark"],
    "Databricks": ["databricks"],
    "Azure": ["azure", "microsoft azure"],
    "AWS": ["aws", "amazon web services"],
    "Snowflake": ["snowflake"],
    "Kafka": ["kafka", "apache kafka"],
    "Python": ["python"],
    "Scala": ["scala"],
    "SQL": ["sql", "t-sql", "pl/sql"],
    "Airflow": ["airflow", "apache airflow"],
    "dbt": ["dbt"],
    "Terraform": ["terraform"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Docker": ["docker"],
    "Power BI": ["power bi", "powerbi"],
    "Synapse": ["synapse", "azure synapse"],
    "Fabric": ["microsoft fabric", "ms fabric"],
    # Estensioni oltre l'elenco iniziale del brief, coerenti col tuo stack:
    "Azure Data Factory": ["azure data factory", "adf"],
    "SQL Server": ["sql server", "mssql"],
    "Git": ["git", "github", "gitlab"],
    "FastAPI": ["fastapi"],
    "Streamlit": ["streamlit"],
    "React": ["react", "react.js", "reactjs"],
}
