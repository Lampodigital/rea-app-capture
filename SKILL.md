---
name: rea-app-capture
description: Raccoglie schermate, flussi, gerarchie UI, video e asset pubblici di app iOS, Android, web o desktop per prepararne la riproduzione con Reverse Engineer Anything (REA). Usare quando si chiede di analizzare, catturare o ricostruire un'app, creare un dossier per REA, o recuperare riferimenti grafici quando screenshot e mirroring risultano neri. Non realizza automaticamente una replica completa.
---

# Cattura app per REA

Prepara un pacchetto verificabile che permetta a REA di ricostruire grafica e comportamento osservabile con il minimo intervento manuale. Rispondi nella lingua dell'utente. Procedi sulle attività già autorizzate; raggruppa soltanto i passaggi che richiedono davvero una persona.

La raccolta e il dossier funzionano anche senza REA installato. In quel caso prepara il passaggio e dichiara che l’analisi REA non è stata eseguita. Gli script richiedono Python 3.10 o successivo; l’estrazione video richiede anche ffmpeg e Pillow, come descritto nel README.

## 1. Identifica il bersaglio e riusa il lavoro esistente

- Conferma da evidenze nome, piattaforma, URL dello store o bundle/package ID, versione osservata e dispositivo. Se il nome è ambiguo, risolvi prima l'identità.
- Cerca dossier, sessioni e bridge già funzionanti nel progetto. Riutilizzali senza reinstallare o azzerare l'app.
- Definisci la copertura in base alla richiesta: schermate, stati e percorsi principali. Non promettere ogni schermata se alcune richiedono acquisti, account o dati indisponibili.
- Inventaria gli strumenti effettivamente disponibili. Per usare REA leggi, se presente, la skill `reverse-engineer-anything` e segui gli strumenti disponibili. Non presumere che REA possa pilotare direttamente un iPhone.

## 2. Avvia subito due percorsi di raccolta

**Osservazione diretta:** usa il browser o il controllo nativo disponibili; su iOS riusa un bridge Appium/XCUITest/WebDriverAgent, su Android gli strumenti ADB/UI disponibili. Leggi [iOS e catture nere](references/ios.md) prima di predisporre un iPhone. Leggi le istruzioni degli strumenti usati; non inventare API o comandi del dispositivo.

**Fonti pubbliche:** cerca subito la scheda corretta dello store, sito ufficiale, demo, trailer e video che mostrano davvero l'app. Non aspettare di risolvere tutti i problemi del dispositivo. Segui [media pubblici](references/public-media.md). Le due attività sono indipendenti quando strumenti e sessioni lo permettono.

Preferisci una prova vuota o con dati sintetici. Non riprendere password, codici, frasi di recupero o contenuti privati. Se l'utente autorizza esplicitamente la gestione di un segreto di prova, conservalo separatamente con accesso ristretto; non inserirlo nel pacchetto per REA. Non confermare che un segreto è stato salvato senza averlo effettivamente preservato o senza che l'utente se ne sia fatto carico.

L'autorizzazione a studiare l'app non implica acquisti, cancellazioni, nuove registrazioni di account/dispositivi, certificati e provisioning, intercettazione del traffico, jailbreak o modifiche alle protezioni. Se necessari e non già autorizzati, prepara il passaggio concreto e chiedi una sola conferma mirata. Riusa le autorizzazioni già espresse nella sessione.

## 3. Cattura gli stati e i collegamenti

Per ogni percorso rilevante:

1. Verifica dispositivo sbloccato, app corretta in primo piano e stato attuale prima di leggere o agire.
2. Salva screenshot originale, gerarchia UI/accessibilità se disponibile e metadati: versione, dimensioni, orientamento, lingua, tema e momento della cattura. Specifica se le coordinate sono punti o pixel.
3. Registra azione, stato iniziale e stato risultante. Rileggi l'interfaccia dopo ogni transizione; non riusare elementi divenuti obsoleti.
4. Copri dove pertinente avvio/onboarding, home, navigazione, creazione/modifica, dettagli, ricerca, impostazioni, vuoto/caricamento/errore, permessi e blocchi premium. Non acquistare per completare la matrice.
5. Cattura animazioni con brevi video se supportati; annota durata e gesto. Una gerarchia UI descrive struttura e testi, non prova colori, font o animazioni.

Se lo screenshot è nero, applica la diagnosi limitata di [iOS](references/ios.md), poi passa alle fonti pubbliche. Segnala che la cattura diretta resta limitata; non dichiararla risolta perché hai trovato screenshot online.

## 4. Costruisci un dossier tracciabile

Segui [schema e criteri del dossier](references/bundle.md). Mantieni distinti:

- osservazione sull'app installata;
- screenshot dello store;
- demo o mockup del sito;
- fotogrammi di video pubblici;
- asset estratti e ritagli derivati;
- ricostruzioni o ipotesi ancora da verificare.

Usa gli script inclusi per il lavoro meccanico:

```sh
python3 <skill-dir>/scripts/evidence_bundle.py init <dossier> --app "Nome app" --platform ios --app-id com.example.app --version unknown
python3 <skill-dir>/scripts/evidence_bundle.py add <dossier> screenshots/home.png --kind live-screenshot --origin "Dispositivo di prova, home" --screen home
python3 <skill-dir>/scripts/extract_video_frames.py demo.mp4 --output <dossier>/frames/demo --times 1,3,5 --source-url https://example.com/demo
python3 <skill-dir>/scripts/evidence_bundle.py validate <dossier>
```

Sostituisci i segnaposto con percorsi reali e passa argomenti al processo senza interpolazioni shell rischiose. Registra solo file selezionati esplicitamente; nessuna scansione automatica di cartelle private. Gli script non scaricano contenuti né installano dipendenze. Registra anche video e fotogrammi nel manifest dopo averli verificati.

## 5. Prepara il passaggio a REA

- Includi un indice leggibile, matrice di copertura, inventario di schermate e componenti, collegamenti tra stati, riferimenti visuali, testi visibili e lacune.
- Importa o analizza con REA solo le fonti pertinenti usando le capacità reali disponibili. Conserva gli ID delle evidenze e i loro rapporti; non inventare un risultato REA se non è stato eseguito.
- Distingui l'analisi statica del sito da quella dell'app nativa. Un file JavaScript promozionale non è il codice iOS. Chiudi eventuali sessioni di analisi native aperte appositamente, senza interrompere sessioni preesistenti utili.
- Nel prompt di passaggio chiedi a REA di citare le evidenze per ogni schermata, distinguere osservazioni e assunzioni, e usare dati sintetici. Indica piattaforma desiderata solo se nota; altrimenti lascia questa scelta esplicita.
- Non dedurre backend, correttezza della crittografia o sicurezza dai soli pixel. Non dichiarare una replica completa, implementata o testata sulla base del dossier.

Concludi indicando dove si trova il pacchetto, quante schermate/fonti sono verificate, cosa manca e quali interventi manuali sono realmente necessari. Nessun invio a terzi o pubblicazione è implicito nella raccolta.
