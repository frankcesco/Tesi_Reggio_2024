import pandas as pd
import numpy as np
import itertools
import os
import json

# Crea la cartella "query_combinazioni" se non esiste
if not os.path.exists('query_combinazioni'):
    os.makedirs('query_combinazioni')

# Carica il file Excel contenente la tabella dei prodotti
df = pd.read_excel('prodotti_finale.xlsx')
print("[DEBUG] Tabella dei prodotti caricata.")


# Funzione per estrarre le top 5 capacità per numero di occorrenze
def get_top_capacities(df, n=5):
    return df['Capacita'].value_counts().head(n).index.tolist()


# Funzione per ottenere i brand con almeno min_results risultati
def get_brands_with_min_results(df, min_results):
    return df['brand'].value_counts()[df['brand'].value_counts() >= min_results].index.tolist()


# Caratteristiche disponibili
min_results = 20
brands = get_brands_with_min_results(df, min_results)
categories = ['Fragranze Donna', 'Fragranze Uomo']
top_capacities = get_top_capacities(df)
olfactory_categories = ['Agrumato', 'Ambrato', 'Aromatico', 'Chypre', 'Cuoio', 'Dolce', 'Floreale', 'Fruttato',
                        'Gourmand', 'Legnoso', 'Muschiato', 'Senza Profumo', 'Speziato Leggero', 'Aromatico Legnoso',
                        'Floreale Fruttato', 'Floreale Legnoso', 'Agrumato Legnoso', 'Agrumato Aromatico',
                        'Agrumato Fruttato', 'Agrumato Floreale', 'Floreale Muschiato', 'Ambrato Floreale',
                        'Agrumato Muschiato']
price_limits = ['<20', '<30', '<40', '<50', '<75', '<100']

print(
    f"[DEBUG] Caratteristiche disponibili: {len(brands)} brand, {len(categories)} categorie, {len(top_capacities)} capacità, {len(olfactory_categories)} categorie olfattive, {len(price_limits)} classi di prezzo.")


# Funzione per filtrare i risultati per ogni combinazione
def filter_results(df, combination):
    results = df.copy()
    print(f"[DEBUG] Filtrando risultati per combinazione: {combination}")

    for feature, value in combination.items():
        if feature == 'brand':
            results = results[results['brand'] == value]
        elif feature == 'category':
            results = results[results['Categorie'].str.contains(value)]
        elif feature == 'capacity':
            results = results[results['Capacita'] == value]
        elif feature == 'olfactory_category':
            results = results[
                results[value] == 1]  # Usa il valore della categoria olfattiva per filtrare la colonna appropriata
        elif feature == 'price':
            results = results[results['prezzo'] < int(value[1:])]

    count_results = len(results)
    print(f"[DEBUG] Risultati filtrati: {count_results} risultati trovati.")
    return results if count_results >= 20 else None


# Funzione per generare tutte le combinazioni di n feature
def generate_combinations(n):
    feature_values = {
        'brand': brands,
        'category': categories,
        'capacity': top_capacities,
        'olfactory_category': olfactory_categories,
        'price': price_limits
    }

    # Ottiene tutte le combinazioni di n feature tra quelle disponibili
    feature_keys = list(feature_values.keys())
    feature_combinations = list(itertools.combinations(feature_keys, n))
    print(f"[DEBUG] Generazione combinazioni per {n} feature: {len(feature_combinations)} combinazioni generate.")

    valid_queries = []

    for feature_combination in feature_combinations:
        print(f"[DEBUG] Elaborazione combinazione: {feature_combination}")

        # Genera tutte le combinazioni dei valori delle feature selezionate
        value_combinations = list(itertools.product(*[feature_values[feature] for feature in feature_combination]))

        for value_combination in value_combinations:
            query = dict(zip(feature_combination, value_combination))
            print(f"[DEBUG] Filtrando risultati per la query: {query}")

            results = filter_results(df, query)

            if results is not None:
                valid_queries.append({'query': query, 'results': results['ID'].tolist()})

    print(f"[DEBUG] Trovate {len(valid_queries)} combinazioni valide.")
    return valid_queries


# Genera e filtra le combinazioni per n = 2, 3 e 4
for n in [2, 3, 4]:
    print(f"[DEBUG] Generazione combinazioni per n = {n}")
    filtered_combinations = generate_combinations(n)

    # Output: lista di combinazioni valide
    print(f"[DEBUG] Trovate {len(filtered_combinations)} combinazioni valide con {n} feature.")

    # Salvataggio delle query valide in un file JSON
    output_filename = f'query_combinazioni/valid_queries_{n}_features.json'
    with open(output_filename, 'w') as f:
        json.dump(filtered_combinations, f, indent=4)

    print(f"[DEBUG] Le query valide per n = {n} sono state salvate in '{output_filename}'.")
