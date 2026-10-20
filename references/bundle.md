# Dossier per REA

## Struttura consigliata

```text
dossier/
  INDEX.md
  coverage.json
  manifest.json
  screenshots/
  ui-trees/
  videos/
  frames/
  crops/
  assets/
  public-sources/
  rea/
```

Adatta la struttura al progetto. Non includere segreti o archivi privati. I file originali restano invariati; trasformazioni e ritagli sono nuovi artefatti.

## Manifest

`evidence_bundle.py` mantiene `manifest.json` con identità dell'app, data UTC e artefatti selezionati. Ogni artefatto contiene ID, percorso relativo, tipo, origine, eventuale URL, schermata, versione osservata, SHA-256 e dimensione. Un derivato può indicare il padre, timestamp e rettangolo di ritaglio `x,y,width,height` in pixel.

Esempio di registrazione di un'immagine pubblica:

```sh
python3 <skill-dir>/scripts/evidence_bundle.py add <dossier> screenshots/store-01.webp --kind store-screenshot --origin "App Store, pagina verificata" --url https://apps.apple.com/example --screen gallery --version unknown
```

L'URL di esempio è un segnaposto. Registra l'URL reale e data di acquisizione; non attribuire automaticamente la versione attuale dello store a media più vecchi.

Per un ritaglio usa `--parent <id>` e `--crop x,y,width,height`; per un fotogramma `--parent <video-id> --timestamp <secondi-locali>`. Registra prima il padre. `--timestamp` riguarda il file padre, non necessariamente il video originale online.

Gli ID `art_…` identificano artefatti locali e non sono ID restituiti da REA. Il formato precedente con ID `ev_…` resta leggibile. Non eseguire più registrazioni contemporaneamente sullo stesso dossier: la sostituzione del manifest è atomica ma non coordina scritture concorrenti.

Il validatore verifica lo schema del manifest, percorso confinato al dossier, presenza, checksum, dimensioni e rapporti padre/figlio. Non certifica identità dell'app, correttezza visuale, liceità di riuso o assenza di dati sensibili: questi richiedono revisione mirata.

## Copertura e indice

Per ogni schermata/stato mantieni una voce con:

- ID e nome;
- precondizioni, azione di accesso, stato finale e collegamenti;
- artefatti visuali e strutturali per ID;
- origine e versione, se nota;
- stato: `observed`, `public-reference`, `partial`, `unverified`, `blocked`;
- dettagli mancanti e motivo concreto.

Nell'indice spiega quali elementi sono verificati: layout, colori/font identificati, testi, icone, spaziature, transizioni, gesti, stati e requisiti. Le misure da video ripreso con una camera sono stime; prospettiva, ritaglio e scala possono alterarle.

## Prompt di passaggio

> Ricostruisci le schermate e i flussi descritti in INDEX.md e coverage.json usando gli artefatti di manifest.json. Per ogni scelta cita gli ID delle evidenze. Distingui osservazioni dirette, riferimenti pubblici e assunzioni. Conserva le lacune come elementi da verificare; non inventare conferme. Usa dati sintetici e non incorporare segreti. La piattaforma di destinazione è [se nota]. Prima di implementare descrivi la copertura ottenibile e i dettagli ancora incerti.

## Criteri di consegna

- Identità dell'app risolta, oppure ambiguità esplicitamente bloccante.
- Copertura utile con evidenze realmente viste; eventuali mancanti elencati.
- Video decodificati e immagini visualmente ispezionate, almeno per ogni stato distinto.
- Checksum e relazioni validi; file sensibili esclusi.
- Nessuna pretesa che mockup o sito provino il codice nativo, il backend o la sicurezza.
- Risultati REA e ID presenti solo se realmente ottenuti; altrimenti pacchetto pronto per importazione con istruzioni.
