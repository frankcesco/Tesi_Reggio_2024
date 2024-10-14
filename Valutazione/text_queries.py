import os
import json
import csv
import subprocess


# Funzione per convertire una query strutturata in una stringa testuale
def convert_in_keywords(query):
    """
    Converte una query strutturata in una stringa testuale con valori in minuscolo,
    seguendo l'ordine specificato: {categoria} {categoria olfattiva} {capacita} {brand} minori di {prezzo} euro.
    """
    result_parts = []
    category = query.get("category", "").strip().lower() if query.get("category") else None
    olfactory_category = query.get("olfactory_category", "").strip().lower() if query.get(
        "olfactory_category") else None
    capacity = query.get("capacity", "").strip().lower() if query.get("capacity") else None
    brand = query.get("brand", "").strip().lower() if query.get("brand") else None
    price = query.get("price", "").replace("<", "").strip() if query.get("price") else None

    if category:
        result_parts.append(category)
    if olfactory_category:
        result_parts.append(olfactory_category)
    if capacity:
        result_parts.append(capacity)
    if brand:
        result_parts.append(brand)
    if price:
        result_parts.append(f"minori di {price} euro")

    result_query = ' '.join(result_parts)
    return result_query


# Funzione per eseguire il comando CLI dockerizzato con la query fornita
def run_docker_wordpress_cli(query):
    """
    Esegue il comando CLI dockerizzato con la query fornita e restituisce il nome del file CSV generato.
    """
    try:
        csv_file = os.path.join(export_dir, f"{query}.csv")
        command = ['docker', 'exec', 'ethos-wordpress-cli-1', 'wp', 'export_clerk_query', query]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Comando eseguito con successo: {query}")
            return csv_file
        else:
            print(f"Errore nell'esecuzione del comando: {result.stderr}")
            return None
    except Exception as e:
        print(f"Errore nell'esecuzione del comando Docker: {str(e)}")
        return None


# Funzione per leggere i risultati dal file CSV
def read_csv_file(csv_file_path):
    """
    Legge il contenuto del file CSV e lo converte in una lista di ID numerici.
    """
    results = []
    if not os.path.exists(csv_file_path):
        print(f"File CSV non trovato: {csv_file_path}")
        return results

    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                results.extend(int(id) for id in row)  # Converti gli ID in numeri interi
        print(f"File CSV letto con successo: {csv_file_path}")
    except Exception as e:
        print(f"Errore nella lettura del file CSV: {str(e)}")

    return sorted(results)


# Funzione per esportare i risultati in un file JSON
def export_to_json(data, output_file):
    """
    Esporta i dati raccolti in formato JSON nel file di output specificato.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"Esportazione in JSON completata: {output_file}")
    except Exception as e:
        print(f"Errore nell'esportazione in JSON: {str(e)}")


# Funzione per processare i file che terminano con SPARQL.json
def process_sparql_files(queries_dir):
    """
    Elenca e processa tutti i file SPARQL.json nella directory specificata.
    """
    for file_name in os.listdir(queries_dir):
        if file_name.endswith('_SPARQL.json'):
            file_path = os.path.join(queries_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    data_list = json.load(json_file)

                print(f"File {file_name} letto con successo.")

                updated_data_list = []
                for data in data_list:
                    if isinstance(data, dict) and 'query' in data:
                        original_query = data.get('query', '')
                        converted_query = convert_in_keywords(original_query)

                        print(f"Esecuzione della query convertita: '{converted_query}'")

                        csv_file = run_docker_wordpress_cli(converted_query)
                        if csv_file and os.path.exists(csv_file):
                            results = read_csv_file(csv_file)
                        else:
                            results = []

                        data['text_query'] = converted_query
                        data['text_results'] = results

                        if os.path.exists(csv_file):
                            try:
                                os.remove(csv_file)
                                print(f"File CSV rimosso: {csv_file}")
                            except Exception as e:
                                print(f"Errore nella rimozione del file CSV: {str(e)}")

                        updated_data_list.append(data)
                    else:
                        print(f"Il file {file_name} contiene dati non validi.")

                output_file = os.path.join(queries_dir, file_name.replace('SPARQL.json', 'final.json'))
                export_to_json(updated_data_list, output_file)

            except Exception as e:
                print(f"Errore nel processare il file {file_name}: {str(e)}")


# Percorsi di file e directory
export_dir = r'C:\Users\franr\Desktop\Repo Sidea\ETHOS\Repo Ethos\ecommerce\ethos\query_exports'
queries_dir = 'query_combinazioni'

# Esegui il processo per tutti i file SPARQL.json
process_sparql_files(queries_dir)
