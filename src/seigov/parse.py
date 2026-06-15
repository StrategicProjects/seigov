"""Conversão das respostas (objetos zeep) para ``pandas.DataFrame``.

Análogo aos tibbles do ``rsei``: estruturas 1:1 viram colunas (achatadas com
``sep``); coleções aninhadas ficam como colunas-objeto (listas de dicts).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _serialize(obj: Any) -> Any:
    """Converte objetos zeep em dict/list nativos; passa dict/list adiante."""
    if obj is None or isinstance(obj, (dict, list)):
        return obj
    try:
        from zeep.helpers import serialize_object

        return serialize_object(obj)
    except Exception:  # pragma: no cover - zeep ausente / objeto simples
        return obj


def to_dataframe(obj: Any, *, sep: str = "_") -> pd.DataFrame:
    """Serializa ``obj`` e devolve um ``DataFrame`` (uma linha por registro)."""
    data = _serialize(obj)
    if data is None:
        return pd.DataFrame()
    if isinstance(data, dict):
        data = [data]
    if isinstance(data, list) and len(data) == 0:
        return pd.DataFrame()
    return pd.json_normalize(data, sep=sep)
