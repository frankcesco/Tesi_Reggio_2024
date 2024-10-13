import json
import pandas as pd
import os

# Percorso al file JSON e al file Excel finale
base_dir = os.path.abspath(os.path.join('..'))
json_file = os.path.join(base_dir, 'all_products.json')
xlsx_file = os.path.join(base_dir, 'informazioni_da_aggiungere_FINALE.xlsx')
output_json_file = os.path.join(base_dir, 'all_products_FINALE.json')

# Carica il file JSON
with open(json_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Estrai il campo "@graph"
products_graph = data.get('@graph', [])

# Leggi il file Excel
print(f"Leggendo il file Excel da: {xlsx_file}")
df = pd.read_excel(xlsx_file)
print(f"Dati letti dal file Excel:\n{df.head()}")

# Crea un dizionario per cercare i dati del file Excel
lookup = {row['permalink']: row for index, row in df.iterrows()}
print(f"Dizionario di ricerca creato. Contiene {len(lookup)} voci.")

# Itera su ogni entità nel campo "@graph" mantenendo tutte le entità
for product in products_graph:
    if product.get('@type') == 'Product':
        # Estrai e modifica il link rimuovendo "/#richSnippet" se presente
        link = product.get('@id', '')
        if link.endswith('/#richSnippet'):
            permalink = link.rsplit('/#richSnippet', 1)[0]
        else:
            permalink = link

        # Controlla se il permalink esiste nel file Excel
        if permalink in lookup:
            info = lookup[permalink]

            # Controlla se il campo 'Capacita' è presente e valido
            if 'Capacita' in info and pd.notna(info['Capacita']):
                if 'additionalProperty' not in product:
                    product['additionalProperty'] = []

                # Aggiungi la capacità solo se non è vuota
                product['additionalProperty'].append({
                    '@type': 'PropertyValue',
                    'name': 'Capacita',
                    'value': info['Capacita']
                })
                # print(f"Aggiunto valore di capacità: {info['Capacita']}")

            # Aggiungi gruppo olfattivo dalla colonna "Categoria Olfattiva", solo se non vuota
            if 'Categoria Olfattiva' in info and pd.notna(info['Categoria Olfattiva']):
                olfactory_categories = info['Categoria Olfattiva']
                if olfactory_categories:  # Controlla che non sia una stringa vuota
                    if 'additionalProperty' not in product:
                        product['additionalProperty'] = []

                    product['additionalProperty'].append({
                        '@type': 'PropertyValue',
                        'name': 'Gruppo Olfattivo',
                        'value': olfactory_categories
                    })
                    # print(f"Aggiunti gruppi olfattivi: {olfactory_categories}")

            # Sostituisci la categoria con quella trovata nel file Excel, solo se non vuota
            if 'Categorie' in info and pd.notna(info['Categorie']):
                product['category'] = info['Categorie']
                # print(f"Sostituita la categoria con: {info['Categorie']}")

# Salva il file JSON aggiornato, mantenendo tutte le entità originali
print(f"Salvando il file JSON aggiornato in: {output_json_file}")
with open(output_json_file, 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=4, ensure_ascii=False)

print("File JSON aggiornato con successo!")