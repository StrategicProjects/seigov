"""seigov — cliente Python para os Web Services SOAP do SEI e do SIP.

Genérico: funciona com qualquer instalação do SEI; informe o endpoint do seu
servidor em :class:`SeiConfig` (ou via ``SEIGOV_URL``).

Exemplo
-------
>>> from seigov import SeiClient
>>> sei = SeiClient(
...     url="https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php",
...     sigla_sistema="MEU_SISTEMA",
...     identificacao_servico="minha-chave",
... )
>>> df = sei.consultar_procedimento("12.1.000000077-4")  # doctest: +SKIP

Aviso: os Web Services do SEI são restritos por IP — só respondem de hosts
autorizados.
"""

from __future__ import annotations

from .client import SeiClient, encode_sin
from .config import SeiConfig, SipConfig
from .exceptions import SeiError, SeiFault
from .parse import to_dataframe
from .sip import SipClient

__version__ = "0.1.1"

__all__ = [
    "SeiClient",
    "SipClient",
    "SeiConfig",
    "SipConfig",
    "SeiError",
    "SeiFault",
    "to_dataframe",
    "encode_sin",
    "__version__",
]
