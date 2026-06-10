# Como colocar no ar (Render) — passo a passo

Você vai precisar de duas contas gratuitas: **GitHub** (onde os arquivos
ficam guardados) e **Render** (onde o app roda). Nada é instalado no seu
computador — tudo pelo navegador.

## Parte 1 — Subir os arquivos pro GitHub

1. Crie uma conta em https://github.com/signup (se ainda não tiver).
2. Logada, clique no **+** no canto superior direito → **New repository**.
3. Nome: `verificador-licencas`. Deixe **Public** marcado.
   Clique em **Create repository**.
4. Na página que abre, clique no link **"uploading an existing file"**.
5. Abra a pasta `license-checker` no seu computador, selecione TUDO que
   está dentro dela (incluindo a pasta `connectors`) e **arraste** pra
   área de upload do GitHub.
   > Importante: arraste o CONTEÚDO da pasta, não a pasta inteira —
   > o arquivo `app.py` precisa ficar na raiz do repositório.
6. Clique no botão verde **Commit changes**.

## Parte 2 — Colocar no ar no Render

1. Crie uma conta em https://render.com — escolha **"Sign up with GitHub"**
   (assim já conecta as duas contas).
2. No painel, clique em **New +** → **Blueprint**.
3. Selecione o repositório `verificador-licencas` e clique em **Connect**.
4. O Render lê o arquivo `render.yaml` e já preenche tudo sozinho.
   Confirme clicando em **Apply** / **Deploy**.
5. Aguarde uns 2–5 minutos (a tela mostra o progresso). Quando aparecer
   **"Live"**, seu app está no ar no endereço mostrado no topo, algo como:

   `https://verificador-licencas.onrender.com`

Pronto — esse link funciona em qualquer computador ou celular, e você
pode compartilhar com a equipe.

### Se o "Blueprint" não aparecer

Dá pra fazer manualmente: **New +** → **Web Service** → selecione o
repositório → preencha:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free

## O que esperar do plano gratuito

- **O app "dorme" após ~15 min sem uso.** O primeiro acesso depois disso
  demora ~50 segundos pra acordar. Os seguintes são normais.
- **O cache da Flórida zera quando o app dorme/reinicia**, então de vez
  em quando a primeira consulta FL vai baixar os CSVs de novo (alguns
  minutos). As consultas seguintes ficam rápidas.
- O endereço é público: qualquer pessoa com o link consegue usar. Os
  dados consultados são registros públicos, então não há problema — mas
  se quiser restringir o acesso depois, dá pra adicionar uma senha
  simples no app.

## Pra atualizar o app no futuro

Edite/substitua os arquivos direto no GitHub (botão **Add file** →
**Upload files** sobrescreve os antigos). O Render percebe a mudança e
republica sozinho em ~2 minutos.
