# Repository del lavoro di tesi di Reggio Francesco Maria

Questo repository contiene il codice sviluppato per l'applicazione del framework proposto nella tesi *"Annotazione Semantica di pagine Web di eCommerce mediante Schema.org ed Applicazione ad un Caso Aziendale"* di Reggio Francesco Maria dell'Università degli Studi di Bari Aldo Moro per l'anno accademico 2023-2024.

Il framework applicato è composto da tre fasi successive di *Annotazione*, in cui il sito è sottoposto alla generazione di annotazioni semantiche, *Raffinamento*, in cui le annotazioni semantiche generate sono migliorate, e di *Valutazione*, in cui si misura il miglioramento nei task di ricerca dovuto all'introduzione delle annotazioni semantiche.

Per ognuna delle tre fasi, è presente una cartella contenente i file sviluppati appositamente per l'applicazione del framework ad un sito di eCommerce realmente esistente. Le tre fasi sono schematizzate nella figura seguente. 

<div align="center">
  <img src="./SLIDES%20annotazione.png" alt="SLIDES Annotazione" width="80%">
</div>

### Contenuto del repository:
- **Scraping dei dati JSON-LD**: Script per estrarre i dati strutturati in JSON-LD dei prodotti dal sito di eCommerce.
- **Raffinamento dei dati strutturati**: Script che inserisce informazioni aggiuntive nei dati strutturati dei prodotti.
- **Classificazione con LLM**: Script per classificare le categorie olfattive a partire dai prodotti.
- **Creazione del corpus dei dati**: Script per creare il corpus dei dati usato nella fase di valutazione.
- **Creazione della ground truth**: Script per la creazione della ground truth della fase di valutazione.
- **Generazione e analisi delle query**: Script per la costruzione ed esecuzione delle query in linguaggio naturale e in SPARQL.
- **Valutazione dei risultati**: Codice per calcolare metriche quantitative di precisione, richiamo e F1 measure sui risultati ottenuti dai sistemi.
- **Traduzione automatica delle query**: Script per tradurre ed eseguire in SPARQL query testuali mediante Large Language Model (LLM).

### Nota:
Il repository non include dati proprietari del sito aziendale né le chiavi delle API utilizzate per il LLM.
