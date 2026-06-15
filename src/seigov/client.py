"""Cliente do SEI sobre ``zeep``.

Constrói o cliente a partir do WSDL empacotado (schema universal do SEI) e
faz *override* do endpoint para o servidor do usuário (``config.url``), tornando
o pacote utilizável com **qualquer** instalação do SEI.

> Acesso restrito por IP: os Web Services do SEI só respondem a requisições
> vindas de hosts previamente autorizados no cadastro do serviço.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from .config import SeiConfig
from .exceptions import SeiError, SeiFault
from .parse import to_dataframe
from .wsdl import sei_wsdl_path

#: QName do binding SOAP do SEI (ns alvo "Sei").
SEI_BINDING = "{Sei}SeiBinding"


def encode_sin(value: bool) -> str:
    """Converte booleano nos sinalizadores S/N do SEI."""
    return "S" if value else "N"


class SeiClient:
    """Cliente dos Web Services do SEI.

    Parameters
    ----------
    config:
        Um :class:`~seigov.config.SeiConfig`. Se omitido, é construído a partir
        de ``**kwargs`` (ex.: ``SeiClient(url=..., sigla_sistema=..., ...)``).
    """

    def __init__(self, config: Optional[SeiConfig] = None, **kwargs: Any):
        self.config = config or SeiConfig(**kwargs)
        if not self.config.url and not self.config.wsdl:
            raise SeiError(
                "Defina `url` (endpoint do Web Service do seu SEI, ex.: "
                "'https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php') ou `wsdl`. "
                "Tambem aceita as variaveis de ambiente SEIGOV_URL / SEIGOV_WSDL."
            )

        from zeep import Client as ZeepClient
        from zeep.transports import Transport

        wsdl = self.config.wsdl or str(sei_wsdl_path())
        self._zeep = ZeepClient(wsdl, transport=Transport(timeout=self.config.timeout))
        # Override do endpoint: usa o schema empacotado + o servidor do usuario.
        if self.config.url:
            self._service = self._zeep.create_service(SEI_BINDING, self.config.url)
        else:
            self._service = self._zeep.service

    # ------------------------------------------------------------------ core
    def call(self, operation: str, *, inject_auth: bool = True, **params: Any):
        """Chama uma operação SOAP do SEI e devolve o objeto zeep (cru).

        Injeta ``SiglaSistema``/``IdentificacaoServico`` por padrão. Traduz
        ``SOAP Fault`` e erros de transporte em :class:`SeiFault`/:class:`SeiError`.
        """
        if inject_auth:
            params = {
                "SiglaSistema": self.config.sigla_sistema,
                "IdentificacaoServico": self.config.identificacao_servico,
                **params,
            }
        from zeep.exceptions import Fault, TransportError

        op = getattr(self._service, operation)
        try:
            return op(**params)
        except Fault as e:  # SOAP Fault do servidor
            raise SeiFault(operation, e) from e
        except (TransportError, ConnectionError, OSError) as e:
            raise SeiError(
                f"Falha ao acessar o SEI em '{self.config.url or self.config.wsdl}' "
                f"(operacao '{operation}'): {e}. Verifique a conectividade e se o "
                f"IP de origem esta autorizado no SEI."
            ) from e

    def _df(self, obj: Any, raw: bool) -> Any:
        return obj if raw else to_dataframe(obj)

    # ------------------------------------------------------------- consultas
    def consultar_procedimento(
        self,
        protocolo_procedimento: str,
        *,
        id_unidade: Optional[str] = None,
        retornar_assuntos: bool = True,
        retornar_interessados: bool = True,
        retornar_observacoes: bool = True,
        retornar_andamento_geracao: bool = True,
        retornar_andamento_conclusao: bool = True,
        retornar_ultimo_andamento: bool = True,
        retornar_unidades_procedimento_aberto: bool = True,
        retornar_procedimentos_relacionados: bool = True,
        retornar_procedimentos_anexados: bool = True,
        raw: bool = False,
    ) -> pd.DataFrame:
        """Consulta um processo (``consultarProcedimento``)."""
        rec = self.call(
            "consultarProcedimento",
            IdUnidade=id_unidade if id_unidade is not None else self.config.id_unidade,
            ProtocoloProcedimento=protocolo_procedimento,
            SinRetornarAssuntos=encode_sin(retornar_assuntos),
            SinRetornarInteressados=encode_sin(retornar_interessados),
            SinRetornarObservacoes=encode_sin(retornar_observacoes),
            SinRetornarAndamentoGeracao=encode_sin(retornar_andamento_geracao),
            SinRetornarAndamentoConclusao=encode_sin(retornar_andamento_conclusao),
            SinRetornarUltimoAndamento=encode_sin(retornar_ultimo_andamento),
            SinRetornarUnidadesProcedimentoAberto=encode_sin(
                retornar_unidades_procedimento_aberto
            ),
            SinRetornarProcedimentosRelacionados=encode_sin(
                retornar_procedimentos_relacionados
            ),
            SinRetornarProcedimentosAnexados=encode_sin(
                retornar_procedimentos_anexados
            ),
        )
        return self._df(rec, raw)

    def consultar_documento(
        self,
        protocolo_documento: str,
        *,
        id_unidade: Optional[str] = None,
        retornar_andamento_geracao: bool = True,
        retornar_assinaturas: bool = True,
        retornar_publicacao: bool = True,
        retornar_campos: bool = True,
        raw: bool = False,
    ) -> pd.DataFrame:
        """Consulta um documento (``consultarDocumento``)."""
        rec = self.call(
            "consultarDocumento",
            IdUnidade=id_unidade if id_unidade is not None else self.config.id_unidade,
            ProtocoloDocumento=protocolo_documento,
            SinRetornarAndamentoGeracao=encode_sin(retornar_andamento_geracao),
            SinRetornarAssinaturas=encode_sin(retornar_assinaturas),
            SinRetornarPublicacao=encode_sin(retornar_publicacao),
            SinRetornarCampos=encode_sin(retornar_campos),
        )
        return self._df(rec, raw)

    # -------------------------------------------------------------- listagens
    def listar_unidades(
        self,
        *,
        id_tipo_procedimento: str = "",
        id_serie: str = "",
        raw: bool = False,
    ) -> pd.DataFrame:
        """Lista as unidades acessíveis ao serviço (``listarUnidades``)."""
        rec = self.call(
            "listarUnidades",
            IdTipoProcedimento=id_tipo_procedimento,
            IdSerie=id_serie,
        )
        return self._df(rec, raw)

    def listar_series(
        self,
        *,
        id_unidade: str = "",
        id_tipo_procedimento: str = "",
        raw: bool = False,
    ) -> pd.DataFrame:
        """Lista os tipos de documento (séries) liberados (``listarSeries``)."""
        rec = self.call(
            "listarSeries",
            IdUnidade=id_unidade,
            IdTipoProcedimento=id_tipo_procedimento,
        )
        return self._df(rec, raw)

    # ----------------------------------------------------------------- lote
    def consultar_procedimentos(
        self, protocolos, *, parar_em_erro: bool = False, **kwargs: Any
    ) -> pd.DataFrame:
        """Consulta vários processos e empilha em um único ``DataFrame``.

        Adiciona as colunas ``protocolo`` e ``erro`` (``None`` em sucesso).
        """
        linhas = []
        for p in protocolos:
            try:
                df = self.consultar_procedimento(str(p), **kwargs)
                df = df.copy()
                df.insert(0, "protocolo", str(p))
                df["erro"] = None
            except SeiError as e:
                if parar_em_erro:
                    raise
                df = pd.DataFrame([{"protocolo": str(p), "erro": str(e)}])
            linhas.append(df)
        return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()
