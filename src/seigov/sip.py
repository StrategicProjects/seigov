"""Cliente do SIP (Sistema de Permissões) sobre ``zeep``.

Namespace ``sipns``, autenticação por ``ChaveAcesso`` + ``IdSistema``.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from .config import SipConfig
from .exceptions import SeiError, SeiFault
from .parse import to_dataframe
from .wsdl import sip_wsdl_path

#: QName do binding SOAP do SIP (ns alvo "sipns").
SIP_BINDING = "{sipns}sipBinding"


class SipClient:
    """Cliente dos Web Services do SIP."""

    def __init__(self, config: Optional[SipConfig] = None, **kwargs: Any):
        self.config = config or SipConfig(**kwargs)
        if not self.config.url and not self.config.wsdl:
            raise SeiError(
                "Defina `url` (endpoint do SIP) ou `wsdl`. Tambem aceita "
                "SEIGOV_SIP_URL / SEIGOV_SIP_WSDL."
            )
        from zeep import Client as ZeepClient
        from zeep.transports import Transport

        wsdl = self.config.wsdl or str(sip_wsdl_path())
        self._zeep = ZeepClient(wsdl, transport=Transport(timeout=self.config.timeout))
        if self.config.url:
            self._service = self._zeep.create_service(SIP_BINDING, self.config.url)
        else:
            self._service = self._zeep.service

    def call(self, operation: str, **params: Any):
        """Chama uma operação do SIP injetando ``ChaveAcesso``."""
        params = {"ChaveAcesso": self.config.chave_acesso, **params}
        from zeep.exceptions import Fault, TransportError

        op = getattr(self._service, operation)
        try:
            return op(**params)
        except Fault as e:
            raise SeiFault(operation, e) from e
        except (TransportError, ConnectionError, OSError) as e:
            raise SeiError(
                f"Falha ao acessar o SIP (operacao '{operation}'): {e}."
            ) from e

    def listar_permissao(
        self,
        *,
        id_orgao_usuario: str = "",
        id_usuario: str = "",
        id_origem_usuario: str = "",
        id_orgao_unidade: str = "",
        id_unidade: str = "",
        id_origem_unidade: str = "",
        id_perfil: str = "",
        raw: bool = False,
    ) -> pd.DataFrame:
        """Lista permissões no SIP (``listarPermissao``)."""
        rec = self.call(
            "listarPermissao",
            IdSistema=self.config.id_sistema,
            IdOrgaoUsuario=id_orgao_usuario,
            IdUsuario=id_usuario,
            IdOrigemUsuario=id_origem_usuario,
            IdOrgaoUnidade=id_orgao_unidade,
            IdUnidade=id_unidade,
            IdOrigemUnidade=id_origem_unidade,
            IdPerfil=id_perfil,
        )
        return rec if raw else to_dataframe(rec)

    def replicar_permissao(self, permissoes: list):
        """Replica (cadastra/altera/exclui) permissões (``replicarPermissao``).

        ``permissoes``: lista de dicts da estrutura ``Permissao`` (ao menos
        ``StaOperacao``, ``IdSistema``, ``IdPerfil``).
        """
        return self.call("replicarPermissao", Permissoes=permissoes)

    def replicar_usuario(self, usuarios: list, *, considerar_orgao: bool = False):
        """Replica (cadastra/altera/desativa/reativa) usuários (``replicarUsuario``).

        ``usuarios``: lista de dicts (ao menos ``StaOperacao`` e ``IdOrigem``).
        """
        return self.call(
            "replicarUsuario",
            Usuarios=usuarios,
            SinConsiderarOrgao="S" if considerar_orgao else "N",
        )
