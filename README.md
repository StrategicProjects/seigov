# seigov <a href="https://github.com/StrategicProjects/seigov"><img src="https://raw.githubusercontent.com/StrategicProjects/seigov/main/docs/seigovHex.svg" align="right" height="130" alt="seigov logo" /></a>

Cliente Python para os **Web Services SOAP do SEI** (Sistema Eletrônico de
Informações) e do **SIP** (Sistema de Permissões). Construído sobre
[`zeep`](https://docs.python-zeep.org/), devolve os resultados como
`pandas.DataFrame`. É a porta Python do pacote R
[`rsei`](https://github.com/StrategicProjects/rsei).

> **⚠️ Acesso restrito por IP.** Os Web Services do SEI só respondem a
> requisições vindas de IPs/servidores previamente autorizados no cadastro do
> serviço. As funções só retornam dados a partir de um host autorizado.

> **Genérico.** O pacote não é amarrado a nenhum órgão: informe o endpoint do
> Web Service do **seu** SEI em `SeiClient(url=...)`.

## Instalação

```bash
pip install seigov            # (após publicação no PyPI)
# ou, do código-fonte:
pip install -e ".[dev]"
```

## Uso

```python
from seigov import SeiClient

sei = SeiClient(
    url="https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php",
    sigla_sistema="MEU_SISTEMA",
    identificacao_servico="minha-chave",   # chave de acesso
)

# Consultar um processo (retorna um DataFrame)
df = sei.consultar_procedimento("12.1.000000077-4")

# Vários de uma vez (empilha; coluna 'erro' isola falhas por linha)
lote = sei.consultar_procedimentos(["12.1.000000077-4", "12.1.000000078-2"])

# Listagens
unidades = sei.listar_unidades()
series   = sei.listar_series()
```

Configuração também por variáveis de ambiente: `SEIGOV_URL`,
`SEIGOV_SIGLA_SISTEMA`, `SEIGOV_IDENTIFICACAO_SERVICO`, `SEIGOV_ID_UNIDADE`.

SIP (permissões):

```python
from seigov import SipClient
sip = SipClient(url="https://sei.<seu-orgao>.gov.br/sip/controlador_ws.php?servico=sip",
                chave_acesso="...", id_sistema="...")
perms = sip.listar_permissao(id_unidade="110000001")
```

## Estado

Em desenvolvimento (Fase 0/1: core + consultas/listagens iniciais). Veja
`PLAN.md` para o roteiro completo (escrita, SIP, helpers em lote/por-processo).

## Licença

GPL-3.0-or-later.
