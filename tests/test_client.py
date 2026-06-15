"""Testes do SeiClient.

- O guard de URL/WSDL roda sem zeep (não importa zeep antes da checagem).
- O teste de chamada constrói o cliente a partir do WSDL empacotado (offline) e
  faz mock do serviço — pulado se zeep não estiver instalado ou se a construção
  exigir rede.
"""

from types import SimpleNamespace

import pytest

from seigov import SeiClient, SeiError
from seigov.client import encode_sin


def test_encode_sin():
    assert encode_sin(True) == "S"
    assert encode_sin(False) == "N"


def test_requer_url_ou_wsdl():
    with pytest.raises(SeiError, match="url"):
        SeiClient(sigla_sistema="X", identificacao_servico="Y")


@pytest.fixture
def sei():
    pytest.importorskip("zeep")
    try:
        client = SeiClient(
            url="http://example.invalid/ws",
            sigla_sistema="SIG",
            identificacao_servico="KEY",
        )
    except Exception as e:  # construção exigiu rede / WSDL incompleto
        pytest.skip(f"construção do cliente indisponível offline: {e}")
    return client


def test_consultar_procedimento_mockado(sei):
    captured = {}

    def fake(**kw):
        captured.update(kw)
        return {
            "IdProcedimento": "10000001",
            "ProcedimentoFormatado": "0000000000.000001/2020-11",
            "TipoProcedimento": {"Nome": "Exemplo"},
        }

    sei._service = SimpleNamespace(consultarProcedimento=fake)
    df = sei.consultar_procedimento("0000000000.000001/2020-11", id_unidade="1")

    # auth injetada + sinalizadores S/N
    assert captured["SiglaSistema"] == "SIG"
    assert captured["IdentificacaoServico"] == "KEY"
    assert captured["SinRetornarAssuntos"] == "S"
    # DataFrame achatado
    assert df.loc[0, "ProcedimentoFormatado"] == "0000000000.000001/2020-11"
    assert df.loc[0, "TipoProcedimento_Nome"] == "Exemplo"


def test_consultar_procedimentos_lote_isola_erro(sei):
    def fake(**kw):
        if kw["ProtocoloProcedimento"] == "BAD":
            from zeep.exceptions import Fault

            raise Fault("processo inexistente")
        return {"ProcedimentoFormatado": kw["ProtocoloProcedimento"]}

    sei._service = SimpleNamespace(consultarProcedimento=fake)
    df = sei.consultar_procedimentos(["0000000000.000001/2020-11", "BAD"])
    assert len(df) == 2
    assert list(df["protocolo"]) == ["0000000000.000001/2020-11", "BAD"]
    bad = df[df["protocolo"] == "BAD"].iloc[0]
    assert bad["erro"] is not None
