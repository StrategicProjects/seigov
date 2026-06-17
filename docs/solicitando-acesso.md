# Solicitando acesso aos Web Services do SEI

Antes de o `seigov` conseguir qualquer resposta, é preciso que o **órgão gestor
da sua instalação do SEI** (em geral a área de TI, autarquia de tecnologia ou
empresa de informática do governo) habilite o consumo dos Web Services para o
seu sistema. Esta página descreve **o que pedir** e **quais dados enviar**, com
base no fluxo típico de solicitação. Os valores aqui são **fictícios e
genéricos** — substitua-os pelos do seu ambiente.

!!! info "Por que isso é necessário"
    Os Web Services do SEI são fechados por padrão. O acesso é liberado por
    *sistema* (uma sigla cadastrada) e restrito aos endereços de rede
    previamente autorizados. Sem esse cadastro e a liberação de IP, todas as
    chamadas falham — independentemente do `seigov`.

## Visão geral do fluxo

1. **Abrir o pedido** com a área gestora do SEI (normalmente via chamado).
2. **Enviar os dados de cadastro** do sistema (lista abaixo).
3. A área **cadastra o sistema** e solicita a **liberação dos IPs** no
   firewall (costuma ser um chamado separado, em outra equipe).
4. **Testar no ambiente de treinamento/homologação** primeiro.
5. Após validar, **solicitar a réplica da configuração em produção**.

Cada instalação do SEI é independente: a sigla, a chave, os endpoints e os
métodos liberados valem **apenas** para aquele ambiente.

## Dados a enviar no pedido

A área gestora normalmente pede os seguintes itens. Um modelo de mensagem:

```text
Prezados, solicitamos a habilitacao do consumo dos Web Services do SEI
para o nosso sistema, nos ambientes de treinamento e producao:

1) Cadastro do Sistema (sigla do "servico")
   Sigla sugerida: MEU_SISTEMA

2) IP(s) do servidor de integracao (IP de saida do orgao)
   - <IP publico do servidor que fara as chamadas>
   - <IP adicional, se houver>
   (sao os enderecos que precisam ser liberados no firewall)

3) Unidades que serao cadastradas
   - Todas  (ou liste as unidades especificas)

4) Tipos de operacao (metodos a liberar) — ver lista abaixo

5) Tipos de processo
   - Todos  (ou liste os tipos especificos)

6) Tipos de documento
   - Todos  (ou deixar em branco)

Faremos os testes primeiro em treinamento e, apos validacao,
solicitaremos a migracao para producao.
```

### 1. Sigla do sistema (`SiglaSistema`)

Um identificador curto do seu sistema, definido por você e cadastrado pela área
gestora (ex.: `MEU_SISTEMA`). É o primeiro parâmetro de toda chamada.

### 2. IPs de saída (liberação de firewall)

!!! warning "Privacidade / LGPD"
    Informe **endereços de rede do servidor**, não dados pessoais. Evite enviar
    nomes de usuários, logins de VPN ou qualquer identificador de pessoa física
    no pedido — eles não são necessários para a liberação e ampliam
    desnecessariamente o tratamento de dados pessoais. A liberação é por **IP
    de saída** do host que fará as chamadas.

Se o seu ambiente sai por um IP dinâmico ou por VPN, alinhe com a equipe de
rede uma faixa fixa ou um IP dedicado.

### 3. Tipos de operação (métodos)

Liste os métodos que pretende usar. Peça apenas o necessário (princípio da
minimização). Exemplos comuns:

```text
consultarProcedimento
consultarProcedimentoIndividual
consultarDocumento
listarAndamentos
listarUsuarios
listarUnidades
gerarProcedimento      # operacoes de escrita — peca so se for usar
incluirDocumento
lancarAndamento
enviarProcesso
definirMarcador
```

Nem todo método existe em toda instalação: dependendo da configuração do
servidor, alguns (p. ex. certas listagens) podem **não estar disponíveis**.
Confirme com a área gestora quais foram efetivamente habilitados.

## A `identificacao_servico` (chave de acesso)

Além da sigla, cada chamada exige uma `IdentificacaoServico` — a **chave de
acesso** do serviço, gerada/definida no cadastro do sistema pela área gestora.
Trate-a como segredo:

- **não** a escreva diretamente no código nem a versione no Git;
- prefira variáveis de ambiente (`SEIGOV_*`) ou um cofre de segredos.

!!! note
    O manual do SEI menciona um modo legado baseado em "Endereço" que será
    descontinuado. Prefira já solicitar a **Chave de Acesso** para evitar
    retrabalho.

## Endpoints (treinamento e produção)

Peça à área gestora a URL do Web Service de cada ambiente. O formato costuma
ser:

```text
https://<host-do-seu-sei>/sei/ws/SeiWS.php                 # SEI principal
https://<host-do-seu-sei>/sip/controlador_ws.php?servico=sip   # SIP (permissoes)
```

Use **treinamento/homologação** para validar tudo — sobretudo as operações de
escrita — antes de tocar em produção.

## Configurando o `seigov` com o que foi liberado

Com a sigla, a chave e a URL em mãos, mantenha os segredos fora do código
usando variáveis de ambiente `SEIGOV_*`:

```bash
export SEIGOV_URL="https://sei.exemplo.gov.br/sei/ws/SeiWS.php"
export SEIGOV_SIGLA_SISTEMA="MEU_SISTEMA"
export SEIGOV_IDENTIFICACAO_SERVICO="sua-chave-de-acesso"
```

```python
from seigov import SeiClient

# Sem argumentos: tudo vem das variaveis de ambiente SEIGOV_*.
sei = SeiClient()

# Teste rapido: uma listagem leve confirma sigla + chave + liberacao de IP.
sei.listar_unidades()
```

Se a chamada retornar dados, o trio **sigla + chave + IP liberado** está
correto. Erros comuns:

- `SeiFault` de autenticação → sigla ou chave incorretas;
- *timeout* / conexão recusada (`SeiError`) → IP ainda não liberado no
  firewall, ou você está chamando de um host diferente do autorizado;
- método "não encontrado" → operação não habilitada naquela instalação.

```python
from seigov import SeiError

try:
    sei.listar_unidades()
except SeiError as e:
    print(e)   # mensagem do servidor; lembre-se da restricao por IP
```

## Boas práticas de privacidade e segurança (LGPD)

Os processos e documentos do SEI frequentemente contêm **dados pessoais** e até
**dados sensíveis**. Ao automatizar consultas com o `seigov`:

- **Minimize**: solicite e consulte apenas os métodos e processos necessários à
  sua finalidade.
- **Não exponha segredos**: chaves de acesso e credenciais nunca devem ir para
  o código-fonte, logs ou repositórios. Use variáveis de ambiente ou um cofre.
- **Cuidado ao salvar respostas**: os `DataFrame` retornados podem conter nomes,
  e-mails e teores de documentos. Trate-os como dados pessoais — controle
  acesso, evite cópias desnecessárias e não os publique.
- **Anonimização em exemplos**: ao compartilhar código, relatórios ou abrir
  *issues*, use protocolos e identificadores **fictícios** (como nesta página),
  nunca dados reais.
- **Respeite o nível de acesso**: o nível de acesso do processo
  (`público`/`restrito`/`sigiloso`) indica a classificação no SEI. Não use o
  Web Service para contornar restrições de acesso.

Documente a **base legal** e a finalidade do tratamento junto à área de
privacidade/encarregado (DPO) do seu órgão antes de colocar a integração em
produção.
