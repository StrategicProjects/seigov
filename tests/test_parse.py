"""Testes do conversor para DataFrame (offline, sem zeep/rede)."""

import pandas as pd

from seigov.parse import to_dataframe


def test_to_dataframe_single_dict():
    df = to_dataframe({"IdProcedimento": "1", "ProcedimentoFormatado": "12.1.0-4"})
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.loc[0, "ProcedimentoFormatado"] == "12.1.0-4"


def test_to_dataframe_list_of_dicts():
    df = to_dataframe([{"Sigla": "A"}, {"Sigla": "B"}])
    assert len(df) == 2
    assert list(df["Sigla"]) == ["A", "B"]


def test_to_dataframe_nested_flatten():
    rec = {"Id": "1", "Unidade": {"Sigla": "ORG", "Descricao": "Org"}}
    df = to_dataframe(rec)
    assert df.loc[0, "Unidade_Sigla"] == "ORG"


def test_to_dataframe_none_and_empty():
    assert to_dataframe(None).empty
    assert to_dataframe([]).empty
