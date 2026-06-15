"""Conversão das respostas (objetos zeep) para ``pandas.DataFrame``.

Análogo aos tibbles do ``rsei``: estruturas 1:1 viram colunas (achatadas com
``sep``); coleções aninhadas ficam como colunas-objeto (listas de dicts).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _serialize(obj: Any) -> Any:
    """Converte objetos zeep (e listas deles) em dict/list nativos.

    Importante: ``serialize_object`` é recursivo — precisa ser aplicado também
    quando ``obj`` é uma lista de objetos zeep (ex.: o array de unidades), senão
    os elementos continuam sendo objetos e o ``json_normalize`` não acha colunas.
    """
    if obj is None:
        return obj
    try:
        from zeep.helpers import serialize_object
    except Exception:  # pragma: no cover - zeep ausente: assume ja serializado
        return obj
    return serialize_object(obj)


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
