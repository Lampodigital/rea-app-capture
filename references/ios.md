# iOS: accesso, cattura e diagnosi limitata

## Prima di installare qualcosa

Riusa bridge, app e sessioni del progetto. Leggi lo stato attuale; non riutilizzare UDID, team, bundle WDA, porte o versioni presi da un caso precedente.

Controlli in sola lettura, se gli strumenti esistono:

```sh
xcode-select -p
xcodebuild -version
xcodebuild -checkFirstLaunchStatus
xcrun devicectl list devices --timeout 15
security find-identity -v -p codesigning
```

Per compilare WebDriverAgent serve Xcode completo; le sole Command Line Tools non bastano. Se manca, verifica i metodi di installazione correnti (App Store o strumenti come xcodes). Login Apple, licenza e conferme sul dispositivo possono richiedere l'utente. Non chiedere password in chat.

Prima di concludere che un'app è assente, leggi l'help corrente del comando di inventario. `devicectl` può elencare solo app di sviluppo per impostazione predefinita: usa le opzioni supportate per includere le altre app e cercare nome/ID esatti. Non basare l'identificazione soltanto sul nome mostrato.

## Bridge operativo

- Dispositivo collegato, abbinato e sbloccato; fiducia nel Mac e Modalità sviluppatore possono richiedere un passaggio manuale. Raggruppa le richieste, poi verifica.
- Per creare un certificato, registrare il dispositivo o generare provisioning usa l'autorizzazione già presente oppure chiedi quella specifica. Non assumere un piano sviluppatore a pagamento.
- Scegli team e bundle di sviluppo reali; non riusare identificativi personali di altre sessioni.
- Associa Appium alla sola interfaccia locale. Se una porta è occupata, scegline una libera; non terminare processi sconosciuti.
- Se la versione installata le supporta, configura `noReset: true`, `fullReset: false`, `shouldTerminateApp: false`, `forceAppLaunch: false` e riusa WDA. Verifica il significato delle opzioni nel driver corrente.
- Non avviare una nuova sessione se quella esistente è utilizzabile. Prima di ogni cattura verifica blocco e app in primo piano con le API effettivamente supportate.
- Endpoint Appium comuni includono screenshot e source; comandi mobili e supporto dipendono dal driver. Leggi documentazione e stato del server prima di usarli.
- I selettori di accessibilità possono differire dal testo visibile. Rileggi la gerarchia e usa un selettore osservato, senza tentativi casuali su pulsanti distruttivi.

Se il telefono si blocca, sospendi cattura e interazioni finché è sbloccato. Non modificare automaticamente blocco schermo o impostazioni di sicurezza per aggirare il problema. Conserva il bridge riutilizzabile, segnala processi e sessioni lasciati attivi.

## Screenshot neri: procedura con limite ai tentativi

1. Conferma app corretta e dispositivo sbloccato; aspetta una transizione realmente in corso, poi prova una cattura stabile.
2. Se nero persiste, confronta una schermata innocua di sistema, evitando notifiche e dati privati. Torna poi all'app. Sistema visibile e app nera indicano una limitazione specifica dell'app osservata; non dimostrano quale tecnica la implementi.
3. Prova al massimo una cattura di elemento o una seconda via supportata se porta nuova informazione. Verifica capacità effettive prima di usare screenshot/video di `devicectl`: non tutti i dispositivi supportano ogni funzione.
4. Se pertinente, prova una sola anteprima USB/QuickTime o mirroring disponibile. Non avviare una lunga registrazione per verificare se il contenuto è visibile. Interrompi una GUI bloccata senza ripetere attese lunghe.
5. Cerca un'eventuale impostazione ufficiale di cattura soltanto nell'interfaccia realmente raggiungibile. Non presumere che esista e non indebolire protezioni senza autorizzazione.
6. Se tutte le vie utili sono nere, registra il limite e usa gerarchie UI, screenshot dello store, sito e video pubblici. Non ricorrere automaticamente a jailbreak o modifica dell'app.

Niente cicli indefiniti di QuickTime, porte o sessioni. Un'anteprima nera osservata anche dall'utente è evidenza sufficiente per passare al percorso alternativo.

## Lezione verificata dal caso Vaultaire

Nel caso originario gerarchie UI e navigazione erano leggibili, mentre catture dell'app e anteprima QuickTime risultavano nere; una schermata di sistema era visibile. Le fonti pubbliche hanno fornito riferimenti grafici utili. Questo dimostra un percorso alternativo di raccolta, non una soluzione al blocco degli screenshot né una regola valida per tutte le app vault.
