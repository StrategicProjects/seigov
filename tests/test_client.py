"""Testes do SeiClient.

- O guard de URL/WSDL roda sem zeep (não importa zeep antes da checagem).
- O teste de chamada constrói o cliente a partir do WSDL empacotado (offline) e
  faz mock do serviço — pulado se zeep não estiver instalado ou se a construção
  exigir rede.
"""

from types import SimpleNamespace

import pandas as pd
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


def test_listar_andamentos_marcadores_mockado(sei):
    captured = {}

    def fake(**kw):
        captured.update(kw)
        return [
            {"IdAndamentoMarcador": "501", "Texto": "Aguardando parecer",
             "DataHora": "07/04/2026 11:20:00",
             "Usuario": {"IdUsuario": "1", "Sigla": "usuario.um", "Nome": "Usuario Um"},
             "Marcador": {"IdMarcador": "10", "Nome": "Urgente", "SinAtivo": "S"}},
            {"IdAndamentoMarcador": "502", "Texto": "Conferido",
             "DataHora": "07/04/2026 16:05:00",
             "Usuario": {"IdUsuario": "2", "Sigla": "usuario.dois", "Nome": "Usuario Dois"},
             "Marcador": {"IdMarcador": "20", "Nome": "Revisado", "SinAtivo": "S"}},
        ]

    sei._service = SimpleNamespace(listarAndamentosMarcadores=fake)
    df = sei.listar_andamentos_marcadores("12.1.0-4", id_unidade="1",
                                          marcadores=["10", "20"])

    # parâmetros montados corretamente (Marcadores vira lista de strings)
    assert captured["SiglaSistema"] == "SIG"
    assert captured["ProtocoloProcedimento"] == "12.1.0-4"
    assert captured["Marcadores"] == ["10", "20"]
    # DataFrame achatado: Usuario_*/Marcador_* viram colunas
    assert list(df["IdAndamentoMarcador"]) == ["501", "502"]
    assert df.loc[0, "Marcador_Nome"] == "Urgente"
    assert df.loc[0, "Usuario_Sigla"] == "usuario.um"


def test_listar_documentos_processo_extrai(sei, monkeypatch):
    tl = pd.DataFrame([
        {"Descricao": "Processo gerado", "DataHora": "07/04/2026 10:00:00",
         "Unidade_Sigla": "A", "Usuario_Sigla": "u1"},
        {"Descricao": "Gerado documento restrito 84230597 (X)",
         "DataHora": "07/04/2026 11:00:00", "Unidade_Sigla": "A", "Usuario_Sigla": "u1"},
        {"Descricao": "Assinado Documento 84230597 (X)",
         "DataHora": "07/04/2026 12:00:00", "Unidade_Sigla": "A", "Usuario_Sigla": "u2"},
        {"Descricao": "Gerado documento restrito 84245389 (Y)",
         "DataHora": "07/04/2026 13:00:00", "Unidade_Sigla": "A", "Usuario_Sigla": "u1"},
    ])
    monkeypatch.setattr(sei, "listar_andamentos_completo", lambda *a, **k: tl)
    docs = sei.listar_documentos_processo("12.1.0-4")
    # dedup, mantém a 1a ocorrência (geração)
    assert list(docs["documento"]) == ["84230597", "84245389"]
    assert docs.iloc[0]["Usuario_Sigla"] == "u1"  # gerou, não quem assinou
