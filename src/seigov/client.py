"""Cliente do SEI sobre ``zeep``.

Constrói o cliente a partir do WSDL empacotado (schema universal do SEI) e
faz *override* do endpoint para o servidor do usuário (``config.url``), tornando
o pacote utilizável com **qualquer** instalação do SEI.

> Acesso restrito por IP: os Web Services do SEI só respondem a requisições
> vindas de hosts previamente autorizados no cadastro do serviço.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import pandas as pd

from .config import SeiConfig
from .exceptions import SeiError, SeiFault
from .parse import to_dataframe
from .wsdl import sei_wsdl_path

#: QName do binding SOAP do SEI (ns alvo "Sei").
SEI_BINDING = "{Sei}SeiBinding"

# regex p/ extrair o número de documento (>=6 dígitos) após a palavra "documento"
_DOC_RE = re.compile(r"[Dd]ocumento[^0-9]*([0-9]{6,})")


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
        if self.config.url:
            self._service = self._zeep.create_service(SEI_BINDING, self.config.url)
        else:
            self._service = self._zeep.service

    # ------------------------------------------------------------------ core
    def call(self, operation: str, *, inject_auth: bool = True, **params: Any):
        """Chama uma operação SOAP do SEI e devolve o objeto zeep (cru).

        Injeta ``SiglaSistema``/``IdentificacaoServico`` por padrão. Traduz
        ``SOAP Fault`` e erros de transporte em :class:`SeiFault`/:class:`SeiError`.
        Qualquer operação do WSDL pode ser chamada por aqui.
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
        except Fault as e:
            raise SeiFault(operation, e) from e
        except (TransportError, ConnectionError, OSError) as e:
            raise SeiError(
                f"Falha ao acessar o SEI em '{self.config.url or self.config.wsdl}' "
                f"(operacao '{operation}'): {e}. Verifique a conectividade e se o "
                f"IP de origem esta autorizado no SEI."
            ) from e

    def _df(self, obj: Any, raw: bool) -> Any:
        return obj if raw else to_dataframe(obj)

    def _un(self, id_unidade: Optional[str]) -> str:
        return id_unidade if id_unidade is not None else self.config.id_unidade

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
            IdUnidade=self._un(id_unidade),
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
            IdUnidade=self._un(id_unidade),
            ProtocoloDocumento=protocolo_documento,
            SinRetornarAndamentoGeracao=encode_sin(retornar_andamento_geracao),
            SinRetornarAssinaturas=encode_sin(retornar_assinaturas),
            SinRetornarPublicacao=encode_sin(retornar_publicacao),
            SinRetornarCampos=encode_sin(retornar_campos),
        )
        return self._df(rec, raw)

    def consultar_publicacao(
        self,
        *,
        id_publicacao: str = "",
        id_documento: str = "",
        protocolo_documento: str = "",
        id_unidade: Optional[str] = None,
        retornar_andamento: bool = True,
        retornar_assinaturas: bool = True,
        raw: bool = False,
    ) -> pd.DataFrame:
        """Consulta uma publicação (``consultarPublicacao``). Informe um de
        ``id_publicacao``/``id_documento``/``protocolo_documento``."""
        if not (id_publicacao or id_documento or protocolo_documento):
            raise SeiError(
                "Informe ao menos um de: id_publicacao, id_documento ou "
                "protocolo_documento."
            )
        rec = self.call(
            "consultarPublicacao",
            IdUnidade=self._un(id_unidade),
            IdPublicacao=id_publicacao,
            IdDocumento=id_documento,
            ProtocoloDocumento=protocolo_documento,
            SinRetornarAndamento=encode_sin(retornar_andamento),
            SinRetornarAssinaturas=encode_sin(retornar_assinaturas),
        )
        return self._df(rec, raw)

    def consultar_bloco(
        self,
        id_bloco: str,
        *,
        id_unidade: Optional[str] = None,
        retornar_protocolos: bool = False,
        raw: bool = False,
    ) -> pd.DataFrame:
        """Consulta um bloco (``consultarBloco``)."""
        rec = self.call(
            "consultarBloco",
            IdUnidade=self._un(id_unidade),
            IdBloco=id_bloco,
            SinRetornarProtocolos=encode_sin(retornar_protocolos),
        )
        return self._df(rec, raw)

    def consultar_procedimento_individual(
        self,
        *,
        id_orgao_procedimento: str,
        id_tipo_procedimento: str,
        id_orgao_usuario: str,
        sigla_usuario: str,
        id_unidade: Optional[str] = None,
        raw: bool = False,
    ) -> pd.DataFrame:
        """Consulta o processo individual mais recente (``consultarProcedimentoIndividual``)."""
        rec = self.call(
            "consultarProcedimentoIndividual",
            IdUnidade=self._un(id_unidade),
            IdOrgaoProcedimento=id_orgao_procedimento,
            IdTipoProcedimento=id_tipo_procedimento,
            IdOrgaoUsuario=id_orgao_usuario,
            SiglaUsuario=sigla_usuario,
        )
        return self._df(rec, raw)

    # -------------------------------------------------------------- listagens
    def listar_unidades(self, *, id_tipo_procedimento="", id_serie="", raw=False):
        """Lista unidades acessíveis ao serviço (``listarUnidades``)."""
        return self._df(self.call("listarUnidades",
                                  IdTipoProcedimento=id_tipo_procedimento,
                                  IdSerie=id_serie), raw)

    def listar_series(self, *, id_unidade="", id_tipo_procedimento="", raw=False):
        """Lista tipos de documento/séries (``listarSeries``)."""
        return self._df(self.call("listarSeries", IdUnidade=id_unidade,
                                  IdTipoProcedimento=id_tipo_procedimento), raw)

    def listar_tipos_procedimento(self, *, id_unidade="", id_serie="", raw=False):
        """Lista tipos de processo (``listarTiposProcedimento``)."""
        return self._df(self.call("listarTiposProcedimento", IdUnidade=id_unidade,
                                  IdSerie=id_serie), raw)

    def listar_tipos_procedimento_ouvidoria(self, *, raw=False):
        """Lista tipos de processo de Ouvidoria (``listarTiposProcedimentoOuvidoria``)."""
        return self._df(self.call("listarTiposProcedimentoOuvidoria"), raw)

    def listar_usuarios(self, *, id_unidade=None, id_usuario="", raw=False):
        """Lista usuários da unidade (``listarUsuarios``)."""
        return self._df(self.call("listarUsuarios", IdUnidade=self._un(id_unidade),
                                  IdUsuario=id_usuario), raw)

    def listar_hipoteses_legais(self, *, id_unidade=None, nivel_acesso="", raw=False):
        """Lista hipóteses legais (``listarHipotesesLegais``)."""
        return self._df(self.call("listarHipotesesLegais", IdUnidade=self._un(id_unidade),
                                  NivelAcesso=nivel_acesso), raw)

    def listar_paises(self, *, id_unidade=None, raw=False):
        """Lista países (``listarPaises``)."""
        return self._df(self.call("listarPaises", IdUnidade=self._un(id_unidade)), raw)

    def listar_estados(self, *, id_unidade=None, id_pais="", raw=False):
        """Lista estados/UF (``listarEstados``)."""
        return self._df(self.call("listarEstados", IdUnidade=self._un(id_unidade),
                                  IdPais=id_pais), raw)

    def listar_cidades(self, *, id_unidade=None, id_pais="", id_estado="", raw=False):
        """Lista cidades (``listarCidades``)."""
        return self._df(self.call("listarCidades", IdUnidade=self._un(id_unidade),
                                  IdPais=id_pais, IdEstado=id_estado), raw)

    def listar_cargos(self, *, id_unidade=None, id_cargo="", raw=False):
        """Lista cargos (``listarCargos``)."""
        return self._df(self.call("listarCargos", IdUnidade=self._un(id_unidade),
                                  IdCargo=id_cargo), raw)

    def listar_contatos(self, *, id_unidade=None, id_tipo_contato="",
                        pagina_registros="", pagina_atual="", sigla="", nome="",
                        cpf="", cnpj="", matricula="", raw=False):
        """Lista contatos (paginado) (``listarContatos``)."""
        return self._df(self.call("listarContatos", IdUnidade=self._un(id_unidade),
                                  IdTipoContato=id_tipo_contato,
                                  PaginaRegistros=pagina_registros, PaginaAtual=pagina_atual,
                                  Sigla=sigla, Nome=nome, CPF=cpf, CNPJ=cnpj,
                                  Matricula=matricula), raw)

    def listar_feriados(self, *, id_unidade=None, id_orgao="", data_inicial="",
                        data_final="", raw=False):
        """Lista feriados (``listarFeriados``)."""
        return self._df(self.call("listarFeriados", IdUnidade=self._un(id_unidade),
                                  IdOrgao=id_orgao, DataInicial=data_inicial,
                                  DataFinal=data_final), raw)

    def listar_extensoes_permitidas(self, *, id_unidade=None, id_arquivo_extensao="",
                                    raw=False):
        """Lista extensões de arquivo permitidas (``listarExtensoesPermitidas``)."""
        return self._df(self.call("listarExtensoesPermitidas",
                                  IdUnidade=self._un(id_unidade),
                                  IdArquivoExtensao=id_arquivo_extensao), raw)

    def listar_marcadores_unidade(self, *, id_unidade=None, raw=False):
        """Lista marcadores da unidade (``listarMarcadoresUnidade``)."""
        return self._df(self.call("listarMarcadoresUnidade",
                                  IdUnidade=self._un(id_unidade)), raw)

    def listar_tipos_conferencia(self, *, id_unidade="", raw=False):
        """Lista tipos de conferência (``listarTiposConferencia``)."""
        return self._df(self.call("listarTiposConferencia", IdUnidade=id_unidade), raw)

    def listar_andamentos(self, protocolo_procedimento, *, id_unidade=None,
                          retornar_atributos=False, andamentos=None, tarefas=None,
                          tarefas_modulos=None, raw=False):
        """Lista andamentos de um processo (``listarAndamentos``). Exige ao menos
        um de ``andamentos``/``tarefas``/``tarefas_modulos``."""
        if andamentos is None and tarefas is None and tarefas_modulos is None:
            raise SeiError("Informe ao menos um de: andamentos, tarefas ou tarefas_modulos.")
        as_list = lambda x: None if x is None else [str(i) for i in x]
        return self._df(self.call("listarAndamentos", IdUnidade=self._un(id_unidade),
                                  ProtocoloProcedimento=protocolo_procedimento,
                                  SinRetornarAtributos=encode_sin(retornar_atributos),
                                  Andamentos=as_list(andamentos),
                                  Tarefas=as_list(tarefas),
                                  TarefasModulos=as_list(tarefas_modulos)), raw)

    def listar_andamentos_marcadores(self, protocolo_procedimento, *, id_unidade=None,
                                     marcadores=None, raw=False):
        """Lista andamentos de marcadores (``listarAndamentosMarcadores``)."""
        as_list = lambda x: None if x is None else [str(i) for i in x]
        return self._df(self.call("listarAndamentosMarcadores",
                                  IdUnidade=self._un(id_unidade),
                                  ProtocoloProcedimento=protocolo_procedimento,
                                  Marcadores=as_list(marcadores)), raw)

    # ---------------------------------------------------------------- escrita
    def gerar_procedimento(self, procedimento, *, id_unidade=None, documentos=None,
                           procedimentos_relacionados=None, unidades_envio=None,
                           manter_aberto_unidade=True, enviar_email_notificacao=False,
                           raw=False, **extra):
        """Gera um novo processo (``gerarProcedimento``). ALTERA dados."""
        rec = self.call("gerarProcedimento", IdUnidade=self._un(id_unidade),
                        Procedimento=procedimento,
                        Documentos=documentos or [],
                        ProcedimentosRelacionados=procedimentos_relacionados or [],
                        UnidadesEnvio=unidades_envio or [],
                        SinManterAbertoUnidade=encode_sin(manter_aberto_unidade),
                        SinEnviarEmailNotificacao=encode_sin(enviar_email_notificacao),
                        **extra)
        return self._df(rec, raw)

    def incluir_documento(self, documento, *, id_unidade=None, raw=False):
        """Inclui um documento (``incluirDocumento``). ALTERA dados."""
        rec = self.call("incluirDocumento", IdUnidade=self._un(id_unidade),
                        Documento=documento)
        return self._df(rec, raw)

    def lancar_andamento(self, protocolo_procedimento, *, id_unidade=None,
                         id_tarefa=None, id_tarefa_modulo=None, atributos=None, raw=False):
        """Lança um andamento (``lancarAndamento``). ALTERA dados."""
        rec = self.call("lancarAndamento", IdUnidade=self._un(id_unidade),
                        ProtocoloProcedimento=protocolo_procedimento,
                        IdTarefa=id_tarefa, IdTarefaModulo=id_tarefa_modulo,
                        Atributos=atributos or [])
        return self._df(rec, raw)

    def enviar_processo(self, protocolo_procedimento, unidades_destino, *, id_unidade=None,
                        manter_aberto_unidade=False, remover_anotacao=False,
                        enviar_email_notificacao=False, reabrir=False):
        """Envia (tramita) um processo (``enviarProcesso``). Retorna o resultado."""
        return self.call("enviarProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento,
                         UnidadesDestino=[str(u) for u in unidades_destino],
                         SinManterAbertoUnidade=encode_sin(manter_aberto_unidade),
                         SinRemoverAnotacao=encode_sin(remover_anotacao),
                         SinEnviarEmailNotificacao=encode_sin(enviar_email_notificacao),
                         SinReabrir=encode_sin(reabrir))

    def _bool_op(self, operation, **params):
        return self.call(operation, IdUnidade=params.pop("IdUnidade", self.config.id_unidade),
                         **params)

    def atribuir_processo(self, protocolo_procedimento, id_usuario, *, id_unidade=None,
                          reabrir=False):
        """Atribui um processo a um usuário (``atribuirProcesso``)."""
        return self.call("atribuirProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento,
                         IdUsuario=id_usuario, SinReabrir=encode_sin(reabrir))

    def concluir_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Conclui um processo na unidade (``concluirProcesso``)."""
        return self.call("concluirProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento)

    def reabrir_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Reabre um processo (``reabrirProcesso``)."""
        return self.call("reabrirProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento)

    def bloquear_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Bloqueia um processo (``bloquearProcesso``)."""
        return self.call("bloquearProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento)

    def desbloquear_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Desbloqueia um processo (``desbloquearProcesso``)."""
        return self.call("desbloquearProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento)

    def excluir_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Exclui um processo (``excluirProcesso``). Irreversível."""
        return self.call("excluirProcesso", IdUnidade=self._un(id_unidade),
                         ProtocoloProcedimento=protocolo_procedimento)

    def cancelar_documento(self, protocolo_documento, motivo, *, id_unidade=None):
        """Cancela um documento (``cancelarDocumento``)."""
        return self.call("cancelarDocumento", IdUnidade=self._un(id_unidade),
                         ProtocoloDocumento=protocolo_documento, Motivo=motivo)

    def excluir_documento(self, protocolo_documento, *, id_unidade=None):
        """Exclui um documento (``excluirDocumento``)."""
        return self.call("excluirDocumento", IdUnidade=self._un(id_unidade),
                         ProtocoloDocumento=protocolo_documento)

    def enviar_email(self, protocolo_procedimento, de, para, assunto, mensagem, *,
                     id_unidade=None, cco=None, id_documentos=None, raw=False):
        """Envia e-mail vinculado a um processo (``enviarEmail``)."""
        join = lambda x: ";".join(x) if isinstance(x, (list, tuple)) else x
        rec = self.call("enviarEmail", IdUnidade=self._un(id_unidade),
                        ProtocoloProcedimento=protocolo_procedimento, De=de,
                        Para=join(para), CCO=join(cco) if cco else "",
                        Assunto=assunto, Mensagem=mensagem,
                        IdDocumentos=[str(d) for d in (id_documentos or [])])
        return self._df(rec, raw)

    def atualizar_contatos(self, contatos, *, id_unidade=None):
        """Atualiza contatos (``atualizarContatos``)."""
        return self.call("atualizarContatos", IdUnidade=self._un(id_unidade),
                         Contatos=contatos)

    # blocos
    def gerar_bloco(self, tipo, descricao, *, id_unidade=None,
                    unidades_disponibilizacao=None, documentos=None,
                    disponibilizar=False):
        """Gera um bloco (``gerarBloco``). Retorna o número do bloco."""
        unidades = [str(u) for u in (unidades_disponibilizacao or [])]
        docs = [str(d) for d in (documentos or [])]
        return self.call("gerarBloco", IdUnidade=self._un(id_unidade), Tipo=tipo,
                         Descricao=descricao, UnidadesDisponibilizacao=unidades,
                         Documentos=docs, SinDisponibilizar=encode_sin(disponibilizar))

    def incluir_documento_bloco(self, id_bloco, protocolo_documento, *, id_unidade=None,
                                anotacao=""):
        """Inclui documento em bloco (``incluirDocumentoBloco``)."""
        return self.call("incluirDocumentoBloco", IdUnidade=self._un(id_unidade),
                         IdBloco=id_bloco, ProtocoloDocumento=protocolo_documento,
                         Anotacao=anotacao)

    def incluir_processo_bloco(self, id_bloco, protocolo_procedimento, *, id_unidade=None,
                               anotacao=""):
        """Inclui processo em bloco (``incluirProcessoBloco``)."""
        return self.call("incluirProcessoBloco", IdUnidade=self._un(id_unidade),
                         IdBloco=id_bloco, ProtocoloProcedimento=protocolo_procedimento,
                         Anotacao=anotacao)

    def disponibilizar_bloco(self, id_bloco, *, id_unidade=None):
        """Disponibiliza um bloco (``disponibilizarBloco``)."""
        return self.call("disponibilizarBloco", IdUnidade=self._un(id_unidade),
                         IdBloco=id_bloco)

    def excluir_bloco(self, id_bloco, *, id_unidade=None):
        """Exclui um bloco (``excluirBloco``)."""
        return self.call("excluirBloco", IdUnidade=self._un(id_unidade), IdBloco=id_bloco)

    # ----------------------------------------------------------------- lote
    def _lote(self, ids, fn, *, id_col="protocolo", parar_em_erro=False, **kwargs):
        linhas = []
        for x in ids:
            try:
                df = fn(str(x), **kwargs).copy()
                df.insert(0, id_col, str(x))
                df["erro"] = None
            except SeiError as e:
                if parar_em_erro:
                    raise
                df = pd.DataFrame([{id_col: str(x), "erro": str(e)}])
            linhas.append(df)
        return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()

    def consultar_procedimentos(self, protocolos, *, parar_em_erro=False, **kwargs):
        """Consulta vários processos e empilha (colunas ``protocolo`` e ``erro``)."""
        return self._lote(protocolos, self.consultar_procedimento,
                          parar_em_erro=parar_em_erro, **kwargs)

    def consultar_documentos(self, protocolos, *, parar_em_erro=False, **kwargs):
        """Consulta vários documentos e empilha (colunas ``protocolo`` e ``erro``)."""
        return self._lote(protocolos, self.consultar_documento,
                          parar_em_erro=parar_em_erro, **kwargs)

    def consultar_publicacoes(self, ids, *, por="id_documento", parar_em_erro=False, **kwargs):
        """Consulta várias publicações e empilha. ``por`` =
        ``id_documento``/``protocolo_documento``/``id_publicacao``."""
        linhas = []
        for x in ids:
            try:
                df = self.consultar_publicacao(**{por: str(x)}, **kwargs).copy()
                df.insert(0, "id", str(x))
                df["erro"] = None
            except SeiError as e:
                if parar_em_erro:
                    raise
                df = pd.DataFrame([{"id": str(x), "erro": str(e)}])
            linhas.append(df)
        return pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()

    # ----------------------------------------------------- helpers por-processo
    def listar_andamentos_completo(self, protocolo_procedimento, *, id_unidade=None,
                                   tarefas=range(1, 201), retornar_atributos=False,
                                   ordenar=True):
        """Linha do tempo completa de andamentos, ordenada por data/hora.

        Como ``listarAndamentos`` exige filtro, usa um intervalo amplo de tarefas.
        """
        df = self.listar_andamentos(protocolo_procedimento, id_unidade=id_unidade,
                                    retornar_atributos=retornar_atributos,
                                    tarefas=list(tarefas))
        if ordenar and not df.empty and "DataHora" in df:
            dt = pd.to_datetime(df["DataHora"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
            df = df.assign(_dt=dt).sort_values("_dt").drop(columns="_dt").reset_index(drop=True)
        return df

    def listar_documentos_processo(self, protocolo_procedimento, *, id_unidade=None,
                                   consultar=False):
        """Documentos de um processo, reconstruídos a partir dos andamentos.

        O WS não lista documentos diretamente; extrai os números das descrições
        (ex.: "Gerado documento ... 84230597"). Heurística — depende do texto.
        """
        tl = self.listar_andamentos_completo(protocolo_procedimento, id_unidade=id_unidade)
        if tl.empty or "Descricao" not in tl:
            return pd.DataFrame(columns=["documento", "DataHora"])
        rows = []
        seen = set()
        for _, r in tl.iterrows():
            m = _DOC_RE.search(str(r.get("Descricao", "")))
            if not m:
                continue
            doc = m.group(1)
            if doc in seen:
                continue
            seen.add(doc)
            rows.append({
                "documento": doc,
                "DataHora": r.get("DataHora"),
                "Unidade_Sigla": r.get("Unidade_Sigla"),
                "Usuario_Sigla": r.get("Usuario_Sigla"),
                "Andamento": r.get("Descricao"),
            })
        docs = pd.DataFrame(rows, columns=["documento", "DataHora", "Unidade_Sigla",
                                           "Usuario_Sigla", "Andamento"])
        if not consultar or docs.empty:
            return docs
        det = self.consultar_documentos(docs["documento"].tolist())
        return docs.merge(det, left_on="documento", right_on="protocolo", how="left",
                          suffixes=("", "_doc"))

    def listar_publicacoes_processo(self, protocolo_procedimento, *, id_unidade=None):
        """Publicações de um processo (documentos do processo que têm publicação)."""
        docs = self.listar_documentos_processo(protocolo_procedimento, id_unidade=id_unidade)
        if docs.empty:
            return pd.DataFrame()
        pubs = self.consultar_publicacoes(docs["documento"].tolist(),
                                          por="protocolo_documento")
        # mantém só os que têm publicação de fato
        for col in ("Publicacao_IdPublicacao", "IdPublicacao"):
            if col in pubs:
                return pubs[pubs[col].notna()].reset_index(drop=True)
        return pubs
