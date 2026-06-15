"""Exceções do seigov."""

from __future__ import annotations


class SeiError(Exception):
    """Erro genérico ao falar com o SEI/SIP (conexão, configuração, timeout)."""


class SeiFault(SeiError):
    """Um ``SOAP Fault`` retornado pelo servidor SEI/SIP.

    Expõe ``code`` e ``message`` (do ``faultcode``/``faultstring``) e a
    operação que falhou, com uma mensagem clara — análogo ao tratamento de
    Fault do pacote R ``rsei``.
    """

    def __init__(self, operation: str, fault):
        self.operation = operation
        self.code = getattr(fault, "code", None)
        self.message = getattr(fault, "message", str(fault))
        super().__init__(
            f"SOAP Fault em '{operation}' [{self.code}]: {self.message}"
        )
