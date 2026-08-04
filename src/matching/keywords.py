from __future__ import annotations

# Catalogo di parole chiave metodologiche/di processo, distinto da
# TECHNOLOGY_CATALOG (Fase 5): qui non cerchiamo tecnologie specifiche ma
# pratiche/metodologie spesso richieste esplicitamente nelle offerte,
# utili per il Matching Engine (Fase 6) per calcolare l'affinità anche
# oltre il semplice stack tecnico.
KEYWORD_CATALOG: dict[str, list[str]] = {
    "Agile": ["agile"],
    "Scrum": ["scrum"],
    "ETL/ELT": ["etl", "elt"],
    "Data Warehouse": ["data warehouse", "datawarehouse", "dwh"],
    "Data Modeling": ["data modeling", "data model", "modellazione dati"],
    "Data Governance": ["data governance", "governance"],
    "Stakeholder Management": ["stakeholder management", "stakeholder"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "DevOps": ["devops"],
    "Mentoring": ["mentoring", "mentorship"],
    "Incremental Loads": ["incremental load", "incremental processing"],
    "Metadata-driven": ["metadata-driven", "metadata driven"],
}
