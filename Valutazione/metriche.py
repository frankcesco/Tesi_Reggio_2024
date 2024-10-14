import json
import os


def calculate_metrics(results1, results2):
    """
    Calcola precisione, richiamo e F1 score per due insiemi di risultati.
    """
    set_results1 = set(map(str, results1))  # Converte in stringhe per evitare problemi di tipi
    set_results2 = set(map(str, results2))

    tp = set_results1.intersection(set_results2)

    # Gestisce la divisione per zero
    if len(set_results1) == 0:
        precision = 0
    else:
        precision = len(tp) / len(set_results1)

    if len(set_results2) == 0:
        recall = 0
    else:
        recall = len(tp) / len(set_results2)

    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * ((precision * recall) / (precision + recall))

    return precision, recall, f1


def evaluate_performance_for_category(data, category_filter):
    """
    Calcola le metriche di precisione, richiamo e F1 per una specifica categoria di query.
    """
    total_precision_sparql = 0
    total_recall_sparql = 0
    total_f1_sparql = 0

    total_precision_text = 0
    total_recall_text = 0
    total_f1_text = 0

    total_precision_llm = 0
    total_recall_llm = 0
    total_f1_llm = 0

    sparql_count = 0
    text_count = 0
    llm_count = 0
    query_count = 0

    for entry in data:
        query = entry.get("query", {})

        if category_filter(query):  # Applica il filtro per la categoria
            query_count += 1  # Conta le query che passano il filtro
            original_results = entry.get("true_results", [])
            sparql_results = entry.get("sparql_results", [])  # Usa 'sparql_results' correttamente
            text_results = entry.get("text_results", [])
            llm_results = entry.get("llm_results", [])  # Aggiungi i risultati della LLM

            if not original_results:
                print("Original results vuoti, salta questa query.")
                continue  # Evita di calcolare metriche con set vuoti

            # Calcolo metriche per sparql_results vs original_results
            precision_sparql, recall_sparql, f1_sparql = calculate_metrics(sparql_results, original_results)
            total_precision_sparql += precision_sparql
            total_recall_sparql += recall_sparql
            total_f1_sparql += f1_sparql
            sparql_count += 1

            # Calcolo metriche per text_results vs original_results
            precision_text, recall_text, f1_text = calculate_metrics(text_results, original_results)
            total_precision_text += precision_text
            total_recall_text += recall_text
            total_f1_text += f1_text
            text_count += 1

            # Calcolo metriche per llm_results vs original_results
            precision_llm, recall_llm, f1_llm = calculate_metrics(llm_results, original_results)
            total_precision_llm += precision_llm
            total_recall_llm += recall_llm
            total_f1_llm += f1_llm
            llm_count += 1

    # Calcola la media per sparql_results
    avg_precision_sparql = total_precision_sparql / sparql_count if sparql_count > 0 else 0
    avg_recall_sparql = total_recall_sparql / sparql_count if sparql_count > 0 else 0
    avg_f1_sparql = total_f1_sparql / sparql_count if sparql_count > 0 else 0

    # Calcola la media per text_results
    avg_precision_text = total_precision_text / text_count if text_count > 0 else 0
    avg_recall_text = total_recall_text / text_count if text_count > 0 else 0
    avg_f1_text = total_f1_text / text_count if text_count > 0 else 0

    # Calcola la media per llm_results
    avg_precision_llm = total_precision_llm / llm_count if llm_count > 0 else 0
    avg_recall_llm = total_recall_llm / llm_count if llm_count > 0 else 0
    avg_f1_llm = total_f1_llm / llm_count if llm_count > 0 else 0

    return {
        "sparql": (avg_precision_sparql, avg_recall_sparql, avg_f1_sparql),
        "text": (avg_precision_text, avg_recall_text, avg_f1_text),
        "llm": (avg_precision_llm, avg_recall_llm, avg_f1_llm),
        "query_count": query_count
    }


def evaluate_performance(json_file, exclude_feature=None):
    """
    Valuta le prestazioni delle query in base a diverse categorie (tutte, senza una feature specifica, con una feature specifica).
    """
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Filtro per tutte le query
    def all_queries(_):
        return True

    # Filtro per query senza la feature specificata
    def without_feature(query):
        return exclude_feature is None or exclude_feature not in query

    # Filtro per query con la feature specificata
    def with_feature(query):
        return exclude_feature is not None and exclude_feature in query

    # Valutazione per tutte le query
    all_results = evaluate_performance_for_category(data, all_queries)

    # Valutazione per query senza la feature specificata
    no_feature_results = evaluate_performance_for_category(data, without_feature)

    # Valutazione per query con la feature specificata
    with_feature_results = evaluate_performance_for_category(data, with_feature)

    # Stampa i risultati
    print(f"\nFile: {json_file}")

    print("Risultati per tutte le query:")
    print(f"Numero di query: {all_results['query_count']}")
    print(
        f"SPARQL - Precisione: {all_results['sparql'][0]:.3f}, Richiamo: {all_results['sparql'][1]:.3f}, F1: {all_results['sparql'][2]:.3f}")
    print(
        f"Text - Precisione: {all_results['text'][0]:.3f}, Richiamo: {all_results['text'][1]:.3f}, F1: {all_results['text'][2]:.3f}")
    print(
        f"LLM - Precisione: {all_results['llm'][0]:.3f}, Richiamo: {all_results['llm'][1]:.3f}, F1: {all_results['llm'][2]:.3f}")

    print(f"\nRisultati per query senza '{exclude_feature}':")
    print(f"Numero di query: {no_feature_results['query_count']}")
    print(
        f"SPARQL - Precisione: {no_feature_results['sparql'][0]:.3f}, Richiamo: {no_feature_results['sparql'][1]:.3f}, F1: {no_feature_results['sparql'][2]:.3f}")
    print(
        f"Text - Precisione: {no_feature_results['text'][0]:.3f}, Richiamo: {no_feature_results['text'][1]:.3f}, F1: {no_feature_results['text'][2]:.3f}")
    print(
        f"LLM - Precisione: {no_feature_results['llm'][0]:.3f}, Richiamo: {no_feature_results['llm'][1]:.3f}, F1: {no_feature_results['llm'][2]:.3f}")

    print(f"\nRisultati per query con '{exclude_feature}':")
    print(f"Numero di query: {with_feature_results['query_count']}")
    print(
        f"SPARQL - Precisione: {with_feature_results['sparql'][0]:.3f}, Richiamo: {with_feature_results['sparql'][1]:.3f}, F1: {with_feature_results['sparql'][2]:.3f}")
    print(
        f"Text - Precisione: {with_feature_results['text'][0]:.3f}, Richiamo: {with_feature_results['text'][1]:.3f}, F1: {with_feature_results['text'][2]:.3f}")
    print(
        f"LLM - Precisione: {with_feature_results['llm'][0]:.3f}, Richiamo: {with_feature_results['llm'][1]:.3f}, F1: {with_feature_results['llm'][2]:.3f}")


def process_all_files(directory, exclude_feature=None):
    """
    Elenca tutti i file JSON nella directory specificata e valuta le prestazioni.
    """
    for filename in os.listdir(directory):
        if filename.endswith('_LLM.json'): # Processa il file con tutti i risultati, pure quelli della LLM
            file_path = os.path.join(directory, filename)
            evaluate_performance(file_path, exclude_feature)


# Directory contenente i file JSON
input_dir = 'query_combinazioni/'

# Feature da escludere (modificabile)
exclude_feature = 'price'

# Processa tutti i file JSON nella directory con la feature da escludere
process_all_files(input_dir, exclude_feature)
