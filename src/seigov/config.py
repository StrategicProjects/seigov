"""Configuração de conexão com o SEI/SIP.

Genérico por design: o pacote **não** embute servidor nem credenciais. Informe
``url`` (endpoint do Web Service do *seu* SEI) e as credenciais, por argumento
ou por variáveis de ambiente ``SEIGOV_*``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, "")
    return v if v else default


@dataclass
class SeiConfig:
    """Configuração do SEI.

    Parameters
    ----------
    url:
        Endpoint do Web Service do SEI do seu órgão, ex.:
        ``"https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php"``. Necessário para
        chamadas reais. Resolve de ``SEIGOV_URL`` se vazio.
    wsdl:
        Opcional. Caminho/URL de um WSDL alternativo. Se vazio, usa o WSDL do
        SEI empacotado (o schema é universal) e o endpoint vem de ``url``.
    sigla_sistema, identificacao_servico:
        Credenciais do serviço (``SiglaSistema`` + chave de acesso). Resolvem de
        ``SEIGOV_SIGLA_SISTEMA`` / ``SEIGOV_IDENTIFICACAO_SERVICO``.
    id_unidade:
        Unidade padrão (muitas operações aceitam vazio). De ``SEIGOV_ID_UNIDADE``.
    timeout:
        Tempo máximo (s) das requisições.
    """

    url: str = ""
    wsdl: str = ""
    sigla_sistema: str = ""
    identificacao_servico: str = ""
    id_unidade: str = ""
    timeout: int = 60

    def __post_init__(self) -> None:
        self.url = self.url or _env("SEIGOV_URL")
        self.wsdl = self.wsdl or _env("SEIGOV_WSDL")
        self.sigla_sistema = self.sigla_sistema or _env("SEIGOV_SIGLA_SISTEMA")
        self.identificacao_servico = (
            self.identificacao_servico or _env("SEIGOV_IDENTIFICACAO_SERVICO")
        )
        self.id_unidade = self.id_unidade or _env("SEIGOV_ID_UNIDADE")


@dataclass
class SipConfig:
    """Configuração do SIP (Sistema de Permissões).

    Autenticação por ``ChaveAcesso`` + ``IdSistema``. Namespace ``sipns``.
    """

    url: str = ""
    wsdl: str = ""
    chave_acesso: str = ""
    id_sistema: str = ""
    timeout: int = 60

    def __post_init__(self) -> None:
        self.url = self.url or _env("SEIGOV_SIP_URL")
        self.wsdl = self.wsdl or _env("SEIGOV_SIP_WSDL")
        self.chave_acesso = self.chave_acesso or _env("SEIGOV_SIP_CHAVE_ACESSO")
        self.id_sistema = self.id_sistema or _env("SEIGOV_SIP_ID_SISTEMA")
