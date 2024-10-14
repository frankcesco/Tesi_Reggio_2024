import json
import requests
import pandas as pd
import os
import subprocess
import csv

# URL del server Fuseki e file Excel con la mappatura URI -> ID
FUSEKI_URL = "http://localhost:3030/ds"
EXCEL_FILE = 'prodotti_finale.xlsx'
EXPORT_DIR = r'C:\Users\franr\Desktop\Repo Sidea\ETHOS\Repo Ethos\ecommerce\ethos\query_exports'
QUERIES_DIR = 'query_combinazioni'

# Funzione per caricare le query da un file JSON
def load_queries(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

# Funzione per generare la query SPARQL
def generate_sparql_query(query_input):
    category_clause = generate_category_clause(query_input.get("category"))
    capacity_clause = generate_capacity_clause(query_input.get("capacity"))
    brand_clause = generate_brand_clause(query_input.get("brand"))
    olfactory_category_clause = generate_olfactory_category_clause(query_input.get("olfactory_category"))
    price_clause = generate_price_clause(query_input.get("price"))

    offer_clause = "?product schema:offers ?offer ." if query_input.get("price") else ""

    sparql_query = f"""
    PREFIX schema: <http://schema.org/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?product
    WHERE {{
      ?product a schema:Product ;
               schema:name ?name .
      {offer_clause}
      {category_clause}
      {capacity_clause}
      {brand_clause}
      {olfactory_category_clause}
      {price_clause}
    }}
    """
    return sparql_query.strip()

# Clausole SPARQL
def generate_category_clause(category):
    return f' ?product schema:category ?category . FILTER(CONTAINS(?category, "{category}")) ' if category else ""

def generate_capacity_clause(capacity):
    return f' ?product schema:additionalProperty [ a schema:PropertyValue ; schema:name "Capacita" ; schema:value "{capacity}" ] . ' if capacity else ""

def generate_brand_clause(brand):
    return f' ?product schema:brand [ a schema:Brand ; schema:name "{brand}" ] . ' if brand else ""

def generate_olfactory_category_clause(olfactory_category):
    return f' ?product schema:additionalProperty [ a schema:PropertyValue ; schema:name "Gruppo Olfattivo" ; schema:value ?olfattivo ] . FILTER(CONTAINS(?olfattivo, "{olfactory_category}")) ' if olfactory_category else ""

def generate_price_clause(price):
    if price:
        max_price = price.replace("<", "").strip()
        return f'''
        ?offer schema:price ?price ;
               schema:priceCurrency ?currency .
        FILTER(xsd:decimal(?price) < {max_price})
        '''
    return ""

# Esegue la query SPARQL sul server Fuseki
def execute_sparql_query(query):
    try:
        response = requests.get(FUSEKI_URL, params={'query': query, 'format': 'json'})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore durante l'esecuzione della query: {e}")
        return None

# Estrazione di URI dai risultati SPARQL
def extract_uris(sparql_results):
    uris = []
    if sparql_results and "results" in sparql_results and "bindings" in sparql_results["results"]:
        for binding in sparql_results["results"]["bindings"]:
            if "product" in binding and "value" in binding["product"]:
                uri = binding["product"]["value"].replace('/#richSnippet', '')
                uris.append(uri)
    return uris

# Caricamento della mappatura URI -> ID dal file Excel
def load_excel_mapping(excel_file):
    df = pd.read_excel(excel_file)
    mapping = dict(zip(df['permalink'], df['ID']))
    return mapping

# Mappa gli URI agli ID
def map_uris_to_ids(uris, mapping):
    ids = [mapping.get(uri, None) for uri in uris]
    return sorted(id for id in ids if id is not None)

# Esecuzione e salvataggio dei risultati delle query
def process_json(input_file, output_file):
    with open(input_file, 'r') as file:
        data = json.load(file)
    
    uri_to_id_mapping = load_excel_mapping(EXCEL_FILE)
    results = []
    
    for entry in data:
        query_input = entry.get("query")
        original_results = entry.get("results")
        
        sparql_query = generate_sparql_query(query_input)
        sparql_results = execute_sparql_query(sparql_query)
        
        uri_list = extract_uris(sparql_results) if sparql_results else []
        id_list = map_uris_to_ids(uri_list, uri_to_id_mapping)
        
        results.append({
            "query": query_input,
            "sparql": sparql_query,
            "sparql_results": id_list,
            "original_results": original_results
        })
    
    with open(output_file, 'w') as file:
        json.dump(results, file, indent=4)
    
    print(f"File JSON salvato come '{output_file}'.")

# Esecuzione di tutti i file JSON
def process_all_json_files(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_SPARQL.json")
            print(f"Elaborazione del file: {input_file}")
            process_json(input_file, output_file)

# Salvataggio dei dati in JSON
def export_to_json(data, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"Esportazione in JSON completata: {output_file}")
    except Exception as e:
        print(f"Errore nell'esportazione in JSON: {str(e)}")

# Esecuzione finale di tutti i file JSON
process_all_json_files(QUERIES_DIR, QUERIES_DIR)
