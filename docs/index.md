# seigov

Cliente Python para os **Web Services SOAP do SEI** (Sistema Eletrônico de
Informações) e do **SIP** (Sistema de Permissões). Construído sobre
[`zeep`](https://docs.python-zeep.org/), devolve os resultados como
`pandas.DataFrame`. É a porta Python do pacote R
[`rsei`](https://github.com/StrategicProjects/rsei).

!!! warning "Acesso restrito por IP"
    Os Web Services do SEI só respondem a requisições vindas de IPs/servidores
    previamente autorizados no cadastro do serviço. As funções só retornam dados
    a partir de um host autorizado.

!!! info "Genérico"
    O pacote não é amarrado a nenhum órgão: informe o endpoint do Web Service do
    **seu** SEI em `SeiClient(url=...)`.

## Instalação

```bash
pip install seigov
```

## Início rápido

```python
from seigov import SeiClient

sei = SeiClient(
    url="https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php",
    sigla_sistema="MEU_SISTEMA",
    identificacao_servico="minha-chave",   # chave de acesso
)

df = sei.consultar_procedimento("12.1.000000077-4")   # -> pandas.DataFrame
unidades = sei.listar_unidades()
```

Veja o [guia de uso](uso.md) e a [referência da API](referencia.md).
