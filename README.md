# Verificador de Licenças Profissionais (EUA) — contractors

App caseiro pra verificar se uma licença de contractor está **ativa e válida**
nos órgãos estaduais oficiais dos EUA.

## Como funciona

Cada estado tem um **conector** em `connectors/`. Há 3 tipos:

| Tipo | Estados | Como funciona |
|---|---|---|
| **Extrato oficial (CSV)** | FL | Baixa os arquivos públicos do DBPR, guarda em `cache/` por 24h e consulta localmente. Rápido e estável. |
| **Scraper** | CA | Consulta a página de detalhe do CSLB pelo número da licença. |
| **Link oficial** | TX, GA, NC, AZ, TN, NV, WA | Devolve o link do portal estadual de verificação (pra abrir e conferir manualmente). Candidatos a virar scraper depois. |

Tudo é normalizado num formato único (`LicenseRecord`), com interpretação
de status: **Válida** (Current/Active), **Não válida** (Delinquent, Expired,
Suspended, Revoked...) ou **Conferir** (status desconhecido).

## Instalação (Windows)

```bat
cd license-checker
pip install -r requirements.txt
```

## Uso — terminal

```bat
python cli.py --states                       :: lista estados
python cli.py FL --license CGC1234567        :: Flórida por número
python cli.py FL --name "SILVA CONSTRUCTION" :: Flórida por nome
python cli.py CA --license 123456            :: Califórnia por número
python cli.py FL --license CGC1234567 --json :: saída em JSON
```

> A primeira consulta na Flórida demora alguns minutos (baixa os CSVs do
> DBPR). Depois fica instantânea por 24h (cache em `cache/`).

## Uso — interface web

```bat
python app.py
```

Abra **http://localhost:8000** — escolha o estado, digite número ou nome.

## Avisos importantes

1. **Layout dos CSVs da Flórida**: os arquivos do DBPR vêm sem cabeçalho.
   O mapeamento de colunas está em `connectors/florida.py` (`FIELD_LAYOUT`).
   Se algum campo aparecer trocado, ajuste conforme o documento oficial
   "Download File Layout Information" em
   https://www2.myfloridalicense.com/construction-industry/public-records/
   Mesmo com layout deslocado, a busca por número funciona (procura em
   todas as colunas).
2. **Scraper da Califórnia**: sites mudam. Se o CSLB alterar a página,
   o app não inventa resultado — mostra "(não interpretado)" com o link
   oficial pra conferência.
3. **Decisão final sempre no portal oficial**: os extratos são atualizados
   periodicamente; pra decisões importantes, confirme no link que o app
   mostra em "Fonte".
4. **Texas**: o estado não licencia general contractor — só ofícios
   (eletricista, HVAC etc.). GC é regulado por cidade/condado.

## Como adicionar/promover um estado

1. Copie `connectors/california.py` (scraper) ou `connectors/florida.py`
   (download de dados) como modelo.
2. Implemente `verify_by_number` retornando `LicenseRecord`s.
3. Registre a classe em `connectors/__init__.py`.

Bons próximos candidatos: **WA** (tem API aberta no data.wa.gov) e
**AZ ROC** (portal Salesforce com endpoint JSON por trás).

## Estrutura

```
license-checker/
├── app.py                 # interface web (FastAPI)
├── cli.py                 # linha de comando
├── requirements.txt
├── cache/                 # CSVs baixados (criado automaticamente)
└── connectors/
    ├── base.py            # LicenseRecord + classe base
    ├── florida.py         # FL — extratos CSV do DBPR
    ├── california.py      # CA — scraper do CSLB
    └── deeplinks.py       # TX, GA, NC, AZ, TN, NV, WA — links oficiais
```
