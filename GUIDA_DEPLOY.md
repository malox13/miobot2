# 🤖 HabitBot — Guida completa al setup

## Cosa serve (tutto gratuito)
- Account **Telegram**
- Account **GitHub** (per caricare il codice)
- Account **Railway** (per far girare il bot)

---

## STEP 1 — Crea il bot su Telegram

1. Apri Telegram e cerca **@BotFather**
2. Scrivi `/newbot`
3. Dai un nome al bot (es. `Le mie abitudini`)
4. Dai uno username (es. `mieabitudini_bot`) — deve finire con `_bot`
5. BotFather ti risponde con un **token** tipo:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. **Copialo e salvalo** — ti servirà dopo

---

## STEP 2 — Carica il codice su GitHub

1. Vai su [github.com](https://github.com) e crea un account (se non ce l'hai)
2. Clicca **"New repository"** (bottone verde in alto a destra)
3. Chiamalo `habitbot`, metti **Private**, clicca **Create repository**
4. Adesso carica i file. Hai due opzioni:

### Opzione A — Via browser (più semplice)
1. Nella pagina del repository, clicca **"uploading an existing file"**
2. Trascina tutti i file della cartella `habitbot` che hai scaricato
3. Clicca **"Commit changes"**

### Opzione B — Via terminale
```bash
cd habitbot
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/TUOUSERNAME/habitbot.git
git push -u origin main
```

---

## STEP 3 — Deploy su Railway

1. Vai su [railway.app](https://railway.app) e clicca **"Start a New Project"**
2. Scegli **"Deploy from GitHub repo"**
3. Autorizza Railway ad accedere a GitHub (clicca "Configure GitHub App")
4. Seleziona il repository `habitbot`
5. Railway inizierà automaticamente a costruire il progetto

### Aggiungi le variabili d'ambiente
6. Nel progetto Railway, vai su **"Variables"** (menù a sinistra)
7. Clicca **"New Variable"** e aggiungi:

   | Nome | Valore |
   |------|--------|
   | `TELEGRAM_BOT_TOKEN` | il token di BotFather (es. `123456789:ABC...`) |
   | `DB_PATH` | `/data/habits.db` |

### Aggiungi il Volume (per il database persistente)
8. Nel progetto Railway, clicca **"+ New"** → **"Volume"**
9. Mount path: `/data`
10. Clicca **"Add"**

### Avvia il deploy
11. Vai su **"Deployments"** e clicca **"Redeploy"** (o aspetta che parta da solo)
12. Controlla i log — dovresti vedere `Bot avviato!`

---

## STEP 4 — Usa il bot!

1. Apri Telegram
2. Cerca il tuo bot per username (es. `@mieabitudini_bot`)
3. Scrivi `/start`
4. Il menu principale apparirà 🎉

---

## Come funziona il bot

### Menu principale
- Mostra tutte le tue attività con stato (⬜ non iniziato, 🟨 parziale, ✅ completo)
- Tocca un'attività per aprire la dashboard
- Usa ➕ per crearne una nuova

### Creare un'attività
1. Tocca **➕ Nuova attività**
2. Scrivi il nome (es. "Leggere libro")
3. Aggiungi voci:
   - **Checkbox** → per cose sì/no (es. "Lettura mattina 20 pagine")
   - **Counter** → per conteggi (es. "Quiz patente" con obiettivo 10)
4. Puoi aggiungere quante voci vuoi
5. Scegli la frequenza: **Giornaliero / Settimanale / Mensile**

### Dashboard attività
- Tocca le checkbox per spuntarle ✅
- Usa ➕/➖ sui counter per incrementare/decrementare
- La barra di progresso si aggiorna in tempo reale

### Reset automatico
- **Giornaliero**: si resetta ogni mezzanotte (ora italiana)
- **Settimanale**: si resetta ogni domenica mezzanotte
- **Mensile**: si resetta all'ultimo giorno del mese mezzanotte

### Statistiche
- Tocca **📊 Stats** in una dashboard per vedere:
  - 🔥 Streak giorni consecutivi
  - 🎯 % di consistenza
  - Storico a blocchi colorati (🟩 completo, 🟨 parziale, 🟥 zero)

---

## Risoluzione problemi

**Il bot non risponde**
→ Controlla i log su Railway (sezione "Deployments" → clicca sul deploy)
→ Verifica che `TELEGRAM_BOT_TOKEN` sia corretto

**I dati spariscono al riavvio**
→ Assicurati di aver aggiunto il Volume su Railway con mount path `/data`
→ Verifica che `DB_PATH` sia impostato su `/data/habits.db`

**"Telegram API error"**
→ Il token potrebbe essere sbagliato — rigeneralo con BotFather usando `/revoke`

---

## Aggiornare il bot

Quando vuoi modificare qualcosa:
1. Modifica i file in locale
2. `git add . && git commit -m "aggiornamento" && git push`
3. Railway fa il redeploy automaticamente in ~1 minuto

---

## Comandi disponibili

| Comando | Funzione |
|---------|----------|
| `/start` | Apre il menu principale |
| `/menu` | Alias di /start |
