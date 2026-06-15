"""Localiza os WSDL empacotados (SEI e SIP).

O WSDL do SEI fica no servidor (restrito por IP). O schema, porém, é o mesmo em
qualquer instalação do SEI — então empacotamos o WSDL e, em tempo de execução,
fazemos *override* do endpoint para o servidor do usuário (ver ``client.py``).
Isso permite construir o cliente offline / em CI.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def sei_wsdl_path() -> Path:
    """Caminho do WSDL do SEI empacotado."""
    return Path(str(files("seigov") / "wsdl" / "sei.wsdl"))


def sip_wsdl_path() -> Path:
    """Caminho do WSDL do SIP empacotado."""
    return Path(str(files("seigov") / "wsdl" / "sip.wsdl"))
