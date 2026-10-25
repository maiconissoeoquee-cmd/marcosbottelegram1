# Marcos — bot de Telegram para jogos e aplicativos Android

O Marcos é um bot de Telegram que entende mensagens do dia a dia em português ("Marcos, me manda o Subway Surfers") e encontra jogos e aplicativos. Ele usa um catálogo local com fontes oficiais, pesquisa em fontes públicas quando o item não está no catálogo, e uma IA (OpenAI) para entender a mensagem. Se a IA estiver fora do ar, ele continua funcionando com regras locais.

**Estado desta entrega:** o catálogo inicial tem **15 entradas** (3 jogos e 12 aplicativos), não 1.000. O importador (`scripts/import_catalog.py`) foi feito para você ampliar a lista depois. Nenhum link foi testado ao vivo nesta entrega.

---

## Parte 1 — Crie o bot no Telegram (5 min)

1. No Telegram, procure **@BotFather** e toque em Iniciar.
2. Envie `/newbot`, escolha um nome (ex.: Marcos) e um nome de usuário que termine em `bot`.
3. O BotFather mostra um **token**. Guarde-o só no seu gerenciador de senhas ou nas variáveis do serviço. **Nunca envie o token para o bot nem para ninguém.**

## Parte 2 — Pegue a chave da IA (opcional, mas recomendado)

1. Crie uma conta em https://platform.openai.com e gere uma chave de API.
2. Adicione créditos. A API é paga por uso; confira os preços atuais no site da OpenAI.
3. Sem chave, o bot continua funcionando com as regras locais.

## Parte 3 — Coloque o projeto no GitHub (pelo celular)

1. Crie uma conta em https://github.com e toque em **New repository**. Nome: `marcos-telegram-bot`. Marque **Private**.
2. Toque em **Add file → Upload files** e envie o conteúdo do ZIP (descompacte antes no celular).
3. Confirme em **Commit changes**.
4. **Não envie o arquivo `.env`.** O `.gitignore` já o bloqueia, mas confira se ele não aparece na lista.

## Parte 4 — Hospede (escolha uma opção)

### Opção A — Docker (computador ou VPS)
1. Copie `.env.example` para `.env` e preencha `TELEGRAM_BOT_TOKEN` e `OPENAI_API_KEY`.
2. Rode `docker compose up -d --build`.
3. Veja os logs com `docker compose logs -f marcos`.

### Opção B — Render (worker, modo polling)
1. Em https://render.com, crie um **New → Blueprint** apontando para o seu repositório (o arquivo `render.yaml` já está pronto).
2. Em **Environment**, cadastre `TELEGRAM_BOT_TOKEN` e `OPENAI_API_KEY` (não ficam no código).
3. Confira o plano e o preço de **Background Worker** antes de criar: workers normalmente são pagos.
4. Em **Logs**, procure a linha `catálogo carregado` e depois `Start polling`.

### Opção C — Termux no Android (rodando no próprio celular)
1. Instale o Termux pela **F-Droid** (a versão da Play Store está desatualizada).
2. No Termux, rode:
   ```
   pkg update && pkg upgrade -y
   pkg install -y python git
   git clone https://github.com/SEU_USUARIO/marcos-telegram-bot.git
   cd marcos-telegram-bot
   python -m venv venv && . venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env        # preencha o token e a chave, depois Ctrl+O, Enter, Ctrl+X
   python -m app.main
   ```
3. Mantenha o celular ligado e o Termux aberto (ou use `termux-wake-lock`). No Android, desative a otimização de bateria para o Termux.

> Observação: "rodar 24 horas" no celular depende da bateria, da rede e do sistema. Para algo permanente, prefira um serviço de nuvem.

## Parte 5 — Testando

Envie no privado do bot:

- `/start`
- `Marcos, me manda o Subway Surfers.`
- `Manda o Shizuku.`
- `Tem FIFA para Android?`
- `Quero baixar um editor de vídeos.`
- `Quais jogos de futebol você tem?`
- `Tem uma versão mais recente desse aplicativo?`
- Depois de uma busca: `Me manda o segundo link` ou `Procura outro site porque esse não funciona`.

## Parte 6 — Trocar ou ampliar o catálogo

1. Crie um arquivo `meus_apps.json` com uma lista de entradas. Modelo:
   ```json
   [
     {
       "id": "meu-app",
       "title": "Meu App",
       "aliases": ["meu app", "meuapp"],
       "type": "app",
       "category": "utilitario",
       "platform": "android",
       "developer": "Nome do desenvolvedor",
       "version": null,
       "official_url": "https://play.google.com/store/apps/details?id=com.exemplo.app",
       "official_source": "Google Play",
       "last_verified": null,
       "mod": null,
       "mod_menu": null
     }
   ]
   ```
2. Valide sem gravar: `python scripts/import_catalog.py meus_apps.json --dry-run`
3. Grave: `python scripts/import_catalog.py meus_apps.json`
4. Reinicie o bot.
5. Confira os links: `python scripts/validate_links.py --online`

Categorias válidas: `acao`, `aventura`, `rpg`, `corrida`, `futebol`, `tiro`, `offline`, `online`, `emulador`, `redes_sociais`, `navegador`, `editor_video`, `utilitario`, `produtividade`, `codigo_aberto`.

**Regra das versões modificadas:** o campo `mod` ou `mod_menu` só aparece para o usuário se `"verified": true` e tiver `"source"`. Deixe `null` quando não houver fonte confiável. Nunca cole um link de APK sem ter conferido a origem.

## Variáveis de ambiente

| Variável | Para que serve |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do BotFather (obrigatório) |
| `OPENAI_API_KEY` | Chave da OpenAI (opcional) |
| `OPENAI_MODEL` | Modelo, padrão `gpt-4o-mini` |
| `RUN_MODE` | `polling` (padrão) ou `webhook` |
| `WEBHOOK_BASE_URL` / `WEBHOOK_SECRET` / `PORT` | Só no modo webhook (URL HTTPS pública) |
| `DB_PATH` | Arquivo SQLite (padrão `marcos.db`) |
| `GITHUB_TOKEN` | Opcional, aumenta o limite da busca no GitHub |
| `CACHE_TTL_SECONDS`, `MAX_INPUT_CHARS`, `AI_TIMEOUT_SECONDS`, `HTTP_TIMEOUT_SECONDS`, `HTTP_MAX_BYTES` | Limites de cache, tamanho, tempo e download |
| `ALLOW_HTTP_LINKS` | Mantenha `false` |

## Resolução de problemas

- **"TELEGRAM_BOT_TOKEN não configurado"**: a variável não foi cadastrada ou o `.env` não está na pasta do projeto.
- **O bot não responde**: confira se o processo está rodando (logs). Ele não responde a mensagens enquanto estiver parado.
- **"IA indisponível, usando regras locais" nos logs**: chave inválida, sem créditos ou sem internet. O bot segue funcionando, só com interpretação mais simples.
- **Nenhum resultado de busca**: a GitHub tem limite sem token; cadastre `GITHUB_TOKEN`. Ou tente o nome oficial do app.
- **Erro de `pip install` no Termux**: rode `pkg install -y clang rust` antes do `pip install -r requirements.txt`.
- **Render não inicia**: confira se `startCommand` é `python -m app.main` e se as variáveis estão cadastradas.
- **Links não abrem**: rode `python scripts/validate_links.py --online` para ver o status de cada um.

## Testes

```
pip install -r requirements.txt
python -m pytest -q
```

## Segurança (resumo)

- Só links HTTPS; esquemas perigosos, IPs privados, hosts locais e credenciais em URL são bloqueados.
- Redirecionamentos são revalidados um a um; respostas têm limite de tamanho e de tempo.
- O bot não baixa, não instala e não executa APKs.
- Resultados de busca nunca são apresentados como verificados ou analisados.
- Se alguém enviar uma chave ou token no chat, o bot recusa e não processa a mensagem.
- Os textos das fontes externas são tratados como dados, nunca como instruções para a IA.

Fontes e licenças dos dados: veja `LICENSE_FONTES.md`.
