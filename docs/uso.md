# Uso

## Configuração

Toda chamada usa um `SeiClient` configurado com o endpoint do seu SEI e as
credenciais do serviço. Os valores também podem vir de variáveis de ambiente
`SEIGOV_*`.

```python
from seigov import SeiClient

sei = SeiClient(
    url="https://sei.<seu-orgao>.gov.br/sei/ws/SeiWS.php",
    sigla_sistema="MEU_SISTEMA",
    identificacao_servico="minha-chave",
    id_unidade="110000001",   # opcional; padrão para as operações
)
```

| Variável de ambiente | Campo |
|---|---|
| `SEIGOV_URL` | `url` |
| `SEIGOV_SIGLA_SISTEMA` | `sigla_sistema` |
| `SEIGOV_IDENTIFICACAO_SERVICO` | `identificacao_servico` |
| `SEIGOV_ID_UNIDADE` | `id_unidade` |

## Consultas

```python
proc = sei.consultar_procedimento("12.1.000000077-4")
doc  = sei.consultar_documento("0003934")
pub  = sei.consultar_publicacao(id_documento="1140000000872")
```

Cada uma devolve um `DataFrame`. Use `raw=True` para o objeto serializado do zeep.

## Listagens

```python
sei.listar_unidades()
sei.listar_series()
sei.listar_tipos_procedimento()
sei.listar_usuarios()
sei.listar_hipoteses_legais()
sei.listar_estados(); sei.listar_cidades(id_estado="...")
```

## Em lote

```python
# empilha num único DataFrame; coluna 'protocolo' + 'erro' (isola falhas)
sei.consultar_procedimentos(["12.1.0001-1", "12.1.0002-2"])
sei.consultar_documentos(["0003934", "0003935"])
```

## Por processo

```python
# linha do tempo completa, ordenada por data/hora
sei.listar_andamentos_completo("12.1.000000077-4")

# eventos de marcador do processo (texto, data/hora, usuário e marcador)
sei.listar_andamentos_marcadores("12.1.000000077-4")

# documentos do processo (reconstruídos a partir dos andamentos)
sei.listar_documentos_processo("12.1.000000077-4")

# publicações do processo
sei.listar_publicacoes_processo("12.1.000000077-4")
```

## Escrita

!!! danger "Operações de escrita alteram dados"
    Valide em ambiente de homologação/treino antes de usar em produção.

```python
sei.gerar_procedimento({"IdTipoProcedimento": "100000368",
                        "Especificacao": "Processo de teste"})
sei.incluir_documento({"Tipo": "G", "IdSerie": "3", "Descricao": "..."})
sei.lancar_andamento("12.1.0001-1", id_tarefa="65",
                     atributos=[{"Nome": "DESCRICAO", "Valor": "texto"}])
sei.enviar_processo("12.1.0001-1", unidades_destino=["110000002"])
```

## SIP (permissões)

```python
from seigov import SipClient

sip = SipClient(
    url="https://sei.<seu-orgao>.gov.br/sip/controlador_ws.php?servico=sip",
    chave_acesso="...", id_sistema="100000100",
)
sip.listar_permissao(id_unidade="110000001")
```

## Erros

Falhas de SOAP viram `SeiFault`; problemas de conexão/timeout viram `SeiError`,
com mensagem clara (lembre-se da restrição por IP).

```python
from seigov import SeiError
try:
    sei.consultar_bloco("999999")
except SeiError as e:
    print(e)
```
