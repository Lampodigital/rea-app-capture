# rea-app-capture

Skill per **Codex e Claude Code** che raccoglie le evidenze necessarie a riprodurre interfaccia e comportamento osservabile di un’app con Reverse Engineer Anything (REA).

Combina osservazione diretta, gerarchie UI, screenshot degli store, asset ufficiali e fotogrammi da demo pubbliche. Quando le catture risultano nere, esegue una diagnosi limitata e usa fonti alternative, indicando le lacune.

La raccolta funziona anche senza REA installato. L’analisi tramite REA richiede i suoi strumenti; il controllo di un iPhone richiede un bridge disponibile, ad esempio Appium/XCUITest/WebDriverAgent. La skill non installa automaticamente questi componenti e non contiene un controller iPhone autonomo. Screenshot e mockup non ricostruiscono automaticamente backend, codice nativo o sicurezza dell’app.

## Installazione in Claude Code

Clona il repository nella cartella delle skill personali:

```sh
git clone https://github.com/Lampodigital/rea-app-capture.git "$HOME/.claude/skills/rea-app-capture"
```

In Claude Code invoca:

```text
/rea-app-capture [nome o URL dell’app]
```

Per renderla disponibile soltanto in un progetto, esegui invece dalla radice del progetto:

```sh
git clone https://github.com/Lampodigital/rea-app-capture.git .claude/skills/rea-app-capture
```

Scegli una sola delle due posizioni per evitare copie divergenti. Il formato `SKILL.md`, con `name` e `description`, è condiviso dai due strumenti; non serve un plugin aggiuntivo. Per i dettagli sul caricamento consulta la [documentazione ufficiale di Claude Code](https://code.claude.com/docs/en/skills).

## Installazione in Codex

Clona il repository pubblico tra le skill, senza inviti o autenticazione GitHub. Il comando rifiuta una destinazione già esistente:

```sh
git clone https://github.com/Lampodigital/rea-app-capture.git "$HOME/.codex/skills/rea-app-capture"
```

Se la cartella esiste già, verifica le modifiche locali prima di aggiornare. Non sovrascriverla alla cieca. Avvia una nuova sessione Codex se la skill non compare tra quelle disponibili.

Invocazione:

```text
Usa $rea-app-capture su [nome o URL dell’app].
Prepara un dossier per REA con schermate, flussi, fonti e dettagli da verificare.
```

## Compatibilità

Le istruzioni e gli script sono gli stessi su Codex e Claude Code. `agents/openai.yaml` contiene soltanto metadati di interfaccia per Codex; il funzionamento della skill non dipende da quel file. Non è necessario aggiungere un `CLAUDE.md` globale o cambiare le autorizzazioni del client.

I browser, i server MCP e REA devono essere disponibili nel client che esegue la skill: una configurazione presente in Codex non viene trasferita automaticamente a Claude Code. Se REA non è collegato, entrambi possono preparare il dossier per una successiva analisi.

I test verificano anche un’installazione isolata nelle cartelle di skill dei due client, eseguendo gli script da una directory esterna. Non avviano sessioni LLM né certificano il controllo di un dispositivo reale.

## Requisiti

- Python 3.10 o successivo. L’inventario `evidence_bundle.py` usa solo la libreria standard.
- Per i video: Pillow per verificare e decodificare realmente le immagini; ffmpeg indicato con `--ffmpeg`, trovato nel PATH, oppure fornito da `imageio-ffmpeg`.
- La procedura interattiva usa i browser e gli strumenti nativi presenti nell’ambiente. Disponibilità e autorizzazioni determinano la copertura.
- Gli script sono verificati automaticamente su Linux e macOS. Non richiedono REA, Xcode o un telefono per eseguire i test sintetici.

Per le dipendenze video, dalla cartella del repository:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-video.txt
```

Gli script non installano dipendenze, non scaricano media, non caricano file e non usano credenziali. Il binario ffmpeg deve provenire da una fonte affidabile. L’estrazione consente a ffmpeg soltanto i protocolli locali `file` e `pipe`, per evitare richieste di rete implicite in playlist locali.

## Strumenti inclusi

Esempio da una copia del repository; il dossier deve essere una cartella nuova, esterna al repository:

```sh
python3 scripts/evidence_bundle.py init ../dossier --app "App di prova" --platform ios --app-id com.example.app
```

Dopo aver acquisito un file autorizzato in `../dossier/screenshots/home.png`:

```sh
python3 scripts/evidence_bundle.py add ../dossier screenshots/home.png --kind live-screenshot --origin "Dispositivo di prova" --screen home
python3 scripts/evidence_bundle.py validate ../dossier
```

Per estrarre fotogrammi da un video locale autorizzato:

```sh
python3 scripts/extract_video_frames.py ../demo.mp4 --output ../dossier/frames/demo --times 1,3,5
```

`--source-url` registra la provenienza, senza effettuare richieste di rete. `--source-start` aggiunge un offset dichiarato, approssimativo, rispetto al video originale. `--times` indica i secondi nel file locale: il frame effettivo dipende dalla cadenza del video e non costituisce una misura temporale esatta. Ogni immagine viene verificata e decodificata con Pillow. Il report non certifica che mostri l’app corretta: serve anche ispezione visuale.

Registra video e fotogrammi nel manifest con `add`; il report `frames.json` da solo non li registra. Il dossier include inoltre indice e matrice di copertura redatti dall’agente secondo [le istruzioni](references/bundle.md).

Gli ID locali `art_…` sono distinti dagli ID di evidenza restituiti da REA. I dossier precedenti con ID `ev_…` sono compatibili se completi e validi. I percorsi nuovi sono normalizzati; i duplicati tramite alias vengono rifiutati anche nei manifest precedenti.

Codici di uscita:

| Comando | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Inventario | Operazione riuscita / dossier valido | Dossier non valido, con report JSON | Argomenti o operazione non validi |
| Video | Tutti i frame decodificati | Almeno un frame fallito, dettagli in `frames.json` | Requisiti, argomenti o destinazione non validi |

Una destinazione video esistente non viene sovrascritta. I frame validi di una cattura parziale rimangono disponibili. Esegui un solo processo di scrittura per dossier; il manifest è sostituito atomicamente ma non ha un lock per scritture concorrenti.

## Test

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

I test generano dati e brevi video sintetici in cartelle temporanee. Coprono schema e integrità dei manifest, derivazioni, percorsi equivalenti e confinamento, immagini corrotte, decodifica reale dei pixel e fallimenti dei video. GitHub Actions esegue la stessa suite; non usa segreti o dispositivi reali.

## Condivisione

Il repository è pubblico: puoi condividere il link per leggere le istruzioni e installare la skill. La visibilità pubblica non concede permessi di scrittura sul repository originale; le modifiche dirette richiedono un accesso autorizzato. Non è inclusa una licenza di redistribuzione pubblica.

Questo repository contiene soltanto la skill e test sintetici. Conserva dossier delle app, media raccolti, credenziali, certificati e dati personali fuori dalla cartella Git. `.gitignore` riduce gli inserimenti accidentali, ma non sostituisce la revisione dei file prima di ogni commit.
