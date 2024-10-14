import pandas as pd
import re
import json
import itertools
import os
from rdflib import Graph


# Funzione per estrarre capacità in millilitri usando espressioni regolari
def extract_capacity(title):
    match = re.search(r'(\d+)\s*(ml|mL|Ml)', title, re.IGNORECASE)
    if match:
        return f"{match.group(1)} ml"
    return None


# Funzione per creare combinazioni alfabetiche di due gruppi olfattivi
def create_combined_olfactory_group(row, group1, group2):
    if row[group1] == 1 and row[group2] == 1:
        return 1
    return 0


# 1. Carica il file Excel con le descrizioni classificate
df = pd.read_excel('prodotti_classificati_finale.xlsx')

# 2. Estrae capacità dai titoli dei post e le aggiunge in una nuova colonna
df['Capacita'] = df['post_title'].apply(extract_capacity)

# Inserisce la colonna "Capacità" nella posizione 6 (indice 5)
df.insert(5, 'Capacita', df.pop('Capacita'))

# Salva il DataFrame temporaneo con le capacità
df.to_excel('prodotti_con_capacità.xlsx', index=False)

# 3. Carica e processa il file JSON per estrarre brand, prezzo e link
json_file = "../all_products.json"
with open(json_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Estrae il campo "@graph"
products_graph = data.get('@graph', [])
products_data = []

# Itera sui prodotti ed estrae il brand, prezzo e il link
for product in products_graph:
    if product.get('@type') == 'Product':
        brand = product.get('brand', {}).get('name', '')
        price = product.get('offers', {}).get('price', '')
        link = product.get('@id', '')
        if link.endswith('/#richSnippet'):
            link = link.rsplit('/#richSnippet', 1)[0]

        products_data.append({
            'link': link,
            'prezzo': price,
            'brand': brand
        })

# Crea un DataFrame con i dati estratti e salvalo
df_prezzi_brand = pd.DataFrame(products_data)
df_prezzi_brand.to_excel('prodotti_prezzi_brand.xlsx', index=False)

# 4. Unisce i file 'prodotti_con_capacità.xlsx' e 'prodotti_prezzi_brand.xlsx'
df_capacità = pd.read_excel('prodotti_con_capacità.xlsx')
df_merged = pd.merge(df_capacità, df_prezzi_brand, left_on='permalink', right_on='link', how='left')

# Salva il DataFrame unito
df_merged.to_excel('prodotti_completi.xlsx', index=False)

# 5. Crea le combinazioni di gruppi olfattivi
olfactory_groups = ['Agrumato', 'Ambrato', 'Aromatico', 'Chypre', 'Cuoio', 'Dolce',
                    'Floreale', 'Fruttato', 'Gourmand', 'Legnoso', 'Muschiato',
                    'Senza Profumo', 'Speziato Leggero']

combinations = list(itertools.combinations(sorted(olfactory_groups), 2))

# Crea un nuovo DataFrame per le combinazioni olfattive
df_combined = pd.DataFrame()

# Aggiunge una colonna per ogni combinazione di gruppi olfattivi
for combo in combinations:
    new_column = f"{combo[0]} {combo[1]}"
    df_combined[new_column] = df_merged.apply(lambda row: create_combined_olfactory_group(row, combo[0], combo[1]),
                                              axis=1)

# Calcola il numero di occorrenze per ciascuna combinazione
combined_olfactory_counts = df_combined.sum()

# Seleziona le top 10 combinazioni per numero di occorrenze
top_10_combined_groups = combined_olfactory_counts.nlargest(10).index.tolist()

# Mantiene solo le colonne corrispondenti alle top 10 combinazioni
df_top_10_combined = df_combined[top_10_combined_groups]

# Aggiunge le top 10 combinazioni al DataFrame originale
df_final = pd.concat([df_merged, df_top_10_combined], axis=1)

# 6. Esporta il risultato finale in un nuovo file Excel
df_final.to_excel('prodotti_finale.xlsx', index=False)

print("File 'prodotti_finale.xlsx' creato con successo!")

# 7. Aggiornamento del file JSON con le nuove informazioni dal file Excel
base_dir = os.path.abspath(os.path.join('..'))
json_file = os.path.join(base_dir, 'all_products.json')
xlsx_file = os.path.join(base_dir, 'prodotti_finale.xlsx')
output_json_file = os.path.join(base_dir, 'all_products_FINALE.json')

# Carica il file JSON
with open(json_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Estrae il campo "@graph"
products_graph = data.get('@graph', [])

# Legge il file Excel con le nuove informazioni
df = pd.read_excel(xlsx_file)

# Crea un dizionario per cercare i dati del file Excel
lookup = {row['permalink']: row for index, row in df.iterrows()}

# Itera su ogni entità nel campo "@graph" mantenendo tutte le entità
for product in products_graph:
    if product.get('@type') == 'Product':
        # Estrae e modifica il link rimuovendo "/#richSnippet" se presente
        link = product.get('@id', '')
        if link.endswith('/#richSnippet'):
            permalink = link.rsplit('/#richSnippet', 1)[0]
        else:
            permalink = link

        # Controlla se il permalink esiste nel file Excel
        if permalink in lookup:
            info = lookup[permalink]

            # Aggiunge la capacità se presente nel file Excel
            if 'Capacita' in info and pd.notna(info['Capacita']):
                if 'additionalProperty' not in product:
                    product['additionalProperty'] = []
                product['additionalProperty'].append({
                    '@type': 'PropertyValue',
                    'name': 'Capacita',
                    'value': info['Capacita']
                })

            # Aggiunge il gruppo olfattivo se presente nel file Excel
            if 'Categoria Olfattiva' in info and pd.notna(info['Categoria Olfattiva']):
                olfactory_categories = info['Categoria Olfattiva']
                if olfactory_categories:
                    if 'additionalProperty' not in product:
                        product['additionalProperty'] = []
                    product['additionalProperty'].append({
                        '@type': 'PropertyValue',
                        'name': 'Gruppo Olfattivo',
                        'value': olfactory_categories
                    })

            # Sostituisce la categoria con quella trovata nel file Excel
            if 'Categorie' in info and pd.notna(info['Categorie']):
                product['category'] = info['Categorie']

# Salva il file JSON aggiornato
with open(output_json_file, 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=4, ensure_ascii=False)

print(f"File JSON aggiornato creato con successo: {output_json_file}")


# 8. Conversione del file JSON-LD in formato Turtle
def convert_json_ld_to_turtle(json_data, output_turtle_file):
    # Crea un grafo RDF
    g = Graph()

    # Parla il JSON-LD nel grafo RDF
    g.parse(data=json.dumps(json_data), format='json-ld')

    # Serializza il grafo in formato Turtle e salva
    g.serialize(destination=output_turtle_file, format='turtle')


# File di input e output per la conversione
turtle_output_file = os.path.join(base_dir, 'all_products_FINALE.ttl')

# Verifica se il file JSON esiste
if os.path.exists(output_json_file):
    print(f"Leggendo il file JSON-LD da: {output_json_file}")

    # Legge il file JSON-LD
    with open(output_json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Converte JSON-LD in Turtle e salva
    convert_json_ld_to_turtle(json_data, turtle_output_file)
    print(f"Conversione in Turtle completata. Salvato il file in: {turtle_output_file}")
else:
    print(f"Il file {output_json_file} non esiste. Conversione non effettuata.")
