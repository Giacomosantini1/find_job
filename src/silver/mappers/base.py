from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypedDict


class SilverRecord(TypedDict):
    """Shape del dizionario prodotto da ogni mapper, allineato 1:1 allo
    schema Spark canonico in `silver/schema.py`. Usare un TypedDict (invece
    di un semplice dict) permette a mypy di segnalare in fase di sviluppo
    se un mapper dimentica un campo o ne scrive uno con nome sbagliato.
    """

    job_id: str
    company: str
    title: str
    location: str | None
    remote: bool | None
    salary: str | None
    description: str | None
    technologies: list[str] | None
    source: str
    publication_date: datetime | None
    link: str | None


class SourceMapper(ABC):
    """Contratto comune per la normalizzazione di un payload grezzo Bronze
    verso lo schema canonico Silver.

    Ogni fonte implementa solo `map`; non deve conoscere né Spark né Delta:
    riceve un dict Python (il JSON grezzo già deserializzato) e restituisce
    un dict Python nello schema comune. Questo rende i mapper testabili in
    isolamento, senza bisogno di una SparkSession nei test unitari.
    """

    source_name: str

    @abstractmethod
    def map(
        self,
        raw_payload: dict[str, Any],
        company_identifier: str,
        source_job_id: str,
        url: str | None,
    ) -> SilverRecord:
        ...

    def build_job_id(self, source_job_id: str) -> str:
        return f"{self.source_name}:{source_job_id}"

    @staticmethod
    def looks_remote(*texts: str | None) -> bool:
        keywords = ("remote", "smart working", "full remote", "telelavoro")
        combined = " ".join(t.lower() for t in texts if t)
        return any(keyword in combined for keyword in keywords)
