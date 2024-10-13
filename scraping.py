import csv
import requests
from bs4 import BeautifulSoup
import json
import os
from rdflib import Graph

# Struttura iniziale fissa con Organization e WebSite
json_data = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": "http://www.ethos.local/#organization",
            "name": "Ethos",
            "url": "http://www.ethos.local"
        },
        {
            "@type": "WebSite",
            "@id": "http://www.ethos.local/#website",
            "url": "http://www.ethos.local",
            "publisher": {
                "@id": "http://www.ethos.local/#organization"
            },
            "inLanguage": "it-IT"
        }
    ]
}


def extract_product_json_ld(url):
    # Effettua la richiesta HTTP all'URL specificato
    response = requests.get(url)

    # Verifica che la richiesta sia andata a buon fine
    if response.status_code == 200:
        # Parsing dell'HTML della pagina
        soup = BeautifulSoup(response.text, "html.parser")

        # Trova tutti gli elementi <script> con type="application/ld+json"
        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        for script in json_ld_scripts:
            try:
                # Carica il contenuto del blocco JSON-LD
                data = json.loads(script.string)
                # Se è presente il tipo "Product", lo aggiungiamo alla lista dei graph
                for item in data.get("@graph", []):
                    if item.get("@type") == "Product":
                        json_data["@graph"].append(item)
                        print(f"Prodotto estratto da {url}")
            except json.JSONDecodeError:
                print(f"Errore nel parsing del JSON-LD da {url}")
    else:
        print(f"Errore nella richiesta: {response.status_code} per {url}")


def convert_json_ld_to_turtle(json_ld_data, output_file):
    # Crea un grafo RDF
    g = Graph()

    # Definisci i prefissi
    g.bind("schema", "http://schema.org/")

    # Aggiungi il JSON-LD al grafo
    g.parse(data=json.dumps(json_ld_data), format="json-ld")

    # Salva il grafo in formato Turtle
    g.serialize(destination=output_file, format="turtle")
    print(f"Salvato il file Turtle in {output_file}")


def save_state(index):
    state_file_path = 'export/state.txt'
    with open(state_file_path, 'w') as state_file:
        state_file.write(str(index))
    print(f"Stato salvato all'indice {index}")


def load_state():
    state_file_path = 'export/state.txt'
    if os.path.exists(state_file_path):
        with open(state_file_path, 'r') as state_file:
            return int(state_file.read().strip())
    return 0


def process_urls(csv_file):
    # Percorso completo del file CSV
    csv_path = os.path.join('export', csv_file)

    # Leggi i permalinks dal file CSV
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        urls = [row['permalink'] for row in reader]

    # Carica lo stato dell'elaborazione
    start_index = load_state()

    # Si assicura che l'indice di partenza non superi la lunghezza della lista
    if start_index > len(urls):
        raise IndexError("L'indice di partenza è maggiore della lunghezza della lista di URL.")

    # Definisce la directory di output
    output_dir = 'export'
    os.makedirs(output_dir, exist_ok=True)

    if start_index < len(urls):
        print(f"Riprendendo da URL numero {start_index + 1}: {urls[start_index]}")

        # Itera attraverso tutti gli URL e processa ciascuno, a partire dall'indice specificato
        for i, url in enumerate(urls[start_index:], start=start_index):
            extract_product_json_ld(url)
            # Salva periodicamente i risultati per evitare perdite di dati
            if (i + 1) % 5 == 0:  # salva ogni 5 URL
                json_output_file = os.path.join(output_dir, 'all_products.json')

                with open(json_output_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print(f"Salvato il file unificato in {json_output_file}")

                # Salva lo stato dell'elaborazione
                save_state(i + 1)

    # Prima di convertire in Turtle, legge il file JSON salvato
    json_output_file = os.path.join(output_dir, 'all_products.json')
    if os.path.exists(json_output_file):
        with open(json_output_file, 'r', encoding='utf-8') as f:
            json_data_from_file = json.load(f)

        # Converte il JSON-LD in Turtle e salva
        turtle_output_file = os.path.join(output_dir, 'all_products.ttl')
        convert_json_ld_to_turtle(json_data_from_file, turtle_output_file)
        print(f"Conversione in Turtle completata. Salvato il file in {turtle_output_file}")
    else:
        print(f"Il file {json_output_file} non esiste. Conversione in Turtle non effettuata.")

if __name__ == '__main__':
    # Nome del file CSV
    csv_file = 'permalinks.csv'

    # Processa tutti gli URL e salva i dati in un unico file JSON e Turtle
    process_urls(csv_file)
