import os
import json
import re
import ast
from langchain_groq import ChatGroq
import requests
import pandas as pd

# Configurazione del ChatGroq
chat = ChatGroq(temperature=0.5, model_name="llama3-groq-70b-8192-tool-use-preview", groq_api_key='example-api-key')

# Definizione del prompt
system = '''
<variabile>
{text_query}
</variabile>

<contesto>
Sei un frontend developer e stai lavorando a un e-commerce. Il tuo compito è leggere una query testuale {text_query} e compilare questi campi:
1) brand = il brand del prodotto.
2) category = la categoria del prodotto.
3) capacity = la capacità in ml del prodotto. Deve essere nel formato "numero ml".
4) olfactory category = la categoria olfattiva del prodotto. Valori possibili: Agrumato, Ambrato, Aromatico, Chypre, Cuoio, Dolce, Floreale, Fruttato, Gourmand, Legnoso, Muschiato, Senza Profumo, Speziato Leggero, Aromatico Legnoso, Floreale Fruttato, Floreale Legnoso, Agrumato Legnoso, Agrumato Aromatico, Agrumato Fruttato, Agrumato Floreale, Floreale Muschiato, Ambrato Floreale, Agrumato Muschiato.
5) price = prezzo massimo in euro. Esempio = minori di 30 euro, meno di 30 euro. Non aggiungere la parola "euro" nel campo.

Ad esempio, se la query è "fragranze donna floreale minori di 30 euro", dovresti compilare questi campi:
1) brand: ""
2) category: "Fragranze Donna"
3) capacity: ""
4) olfactory category: "Floreale"
5) price: "< 30"

Se una parola viene inserita in un campo, non può essere inserita in un altro campo. Ad esempio, se "floreale" è inserito in "olfactory category", non può essere inserito in "category". Usa la feature più probabile per ogni parola.

</contesto>

<istruzioni>
1. Leggi la "{text_query}".
2. Per ogni feature, cerca la corrispondenza nella query e compila il campo.
3. Ogni parola in {text_query} può corrispondere a una sola feature.
4. Se non trovi una corrispondenza, lascia il campo vuoto.
5. Esegui l'output in formato lista di liste di Python, come indicato nel tag <output>.
</istruzioni>

<output>
[ ["brand", value], ["category", value], ["capacity", value ' ml'], ["olfactory category", value], ["price", '< ' value] ]
</output>
'''

from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate

prompt = ChatPromptTemplate(
    input_variables=['text_query'],
    messages=[
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=['text_query'],
                template=system
            )
        )
    ]
)

chain = prompt | chat


def validate_output_format(llm_output):
    print("Validazione output...")
    try:
        llm_output = ast.literal_eval(llm_output)

        if not isinstance(llm_output, list) or len(llm_output) != 5:
            print(f"Errore: l'output non è una lista di 5 liste. Output ricevuto: {llm_output}")
            return False

        for field in llm_output:
            if len(field) != 2:
                print(f"Errore: il campo non ha lunghezza 2. Campo ricevuto: {field}")
                return False

            field_name, field_value = field

            if field_name in ["brand", "category", "olfactory category"]:
                if not (isinstance(field_value, str) or field_value == ""):
                    print(f"Errore: '{field_name}' non è una stringa o vuoto. Valore ricevuto: {field_value}")
                    return False

            if field_name == "capacity":
                if field_value and not re.match(r"^\d+ ml$", field_value):
                    print(f"Errore: la capacità non è nel formato corretto. Valore ricevuto: {field_value}")
                    return False

            if field_name == "price":
                if field_value and not re.match(r"^< \d+$", field_value):
                    print(f"Errore: il prezzo non è nel formato corretto. Valore ricevuto: {field_value}")
                    return False

        print("Output valido!")
        return True
    except Exception as e:
        print(f"Errore nella validazione: {e}")
        return False


def capitalize_fields(llm_output):
    print("Capitalizzazione campi...")
    capitalized_output = []

    def capitalize_words(text):
        return ' '.join(word.capitalize() for word in text.split())

    for field in llm_output:
        name, value = field
        if name == "capacity" and value:
            capitalized_output.append([name, value.lower()])
        else:
            capitalized_output.append([name, capitalize_words(value)])
    print(f"Output capitalizzato: {capitalized_output}")
    return capitalized_output


def generate_sparql_query(query_input):
    category_clause = generate_category_clause(query_input.get("category"))
    capacity_clause = generate_capacity_clause(query_input.get("capacity"))
    brand_clause = generate_brand_clause(query_input.get("brand"))
    olfactory_category_clause = generate_olfactory_category_clause(query_input.get("olfactory category"))
    price_clause = generate_price_clause(query_input.get("price"))

    if query_input.get("price"):
        offer_clause = "?product schema:offers ?offer ."
    else:
        offer_clause = ""

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


def generate_category_clause(category):
    if category:
        return f' ?product schema:category ?category . FILTER(CONTAINS(?category, "{category}")) '
    return ""


def generate_capacity_clause(capacity):
    if capacity:
        return f' ?product schema:additionalProperty [ a schema:PropertyValue ; schema:name "Capacita" ; schema:value "{capacity}" ] . '
    return ""


def generate_brand_clause(brand):
    if brand:
        return f' ?product schema:brand [ a schema:Brand ; schema:name "{brand}" ] . '
    return ""


def generate_olfactory_category_clause(olfactory_category):
    if olfactory_category:
        return f' ?product schema:additionalProperty [ a schema:PropertyValue ; schema:name "Gruppo Olfattivo" ; schema:value ?olfattivo ] . FILTER(CONTAINS(?olfattivo, "{olfactory_category}")) '
    return ""


def generate_price_clause(price):
    if price:
        max_price = price.replace("<", "").strip()
        return f'''
        ?offer schema:price ?price ;
               schema:priceCurrency ?currency .
        FILTER(xsd:decimal(?price) < {max_price})
        '''
    return ""


# URL del tuo server Fuseki
FUSEKI_URL = "http://localhost:3030/ds"
EXCEL_FILE = 'prodotti_finale.xlsx'


def execute_sparql_query(query):
    """Esegue una query SPARQL sul server Fuseki e restituisce i risultati."""
    try:
        response = requests.get(FUSEKI_URL, params={'query': query, 'format': 'json'})
        response.raise_for_status()  # Assicurati che la richiesta abbia avuto successo
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore durante l'esecuzione della query: {e}")
        return None


def extract_uris(sparql_results):
    """Estrae una lista di URI dai risultati SPARQL."""
    uris = []
    if sparql_results and "results" in sparql_results and "bindings" in sparql_results["results"]:
        for binding in sparql_results["results"]["bindings"]:
            if "product" in binding and "value" in binding["product"]:
                uri = binding["product"]["value"].replace('/#richSnippet', '')
                uris.append(uri)
    return uris


def load_excel_mapping(excel_file):
    """Carica il file Excel e restituisce un dizionario di mappatura URI -> ID."""
    df = pd.read_excel(excel_file)
    mapping = dict(zip(df['permalink'], df['ID']))
    return mapping


def map_uris_to_ids(uris, mapping):
    """Mappa gli URI agli ID usando il dizionario di mappatura."""
    ids = [mapping.get(uri, None) for uri in uris]
    return sorted(id for id in ids if id is not None)


# Carica e processa i file JSON nella cartella
json_folder = 'query_combinazioni/'
for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        file_path = os.path.join(json_folder, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Crea una nuova lista per i risultati aggiornati
        updated_data = []

        # Itera attraverso ogni oggetto nel JSON
        for query_obj in data:
            text_query = query_obj.get("text_query", "")

            print(f"\nProcessando la query: {text_query}")
            valid_output = False
            while not valid_output:
                result = chain.invoke({"text_query": text_query})
                llm_output = result.content  # Estrai il contenuto della LLM
                print(f"Output generato dalla LLM: {llm_output}")

                valid_output = validate_output_format(llm_output)
                if not valid_output:
                    print(f"L'output generato non è valido. Rigenerazione...")

            extracted_fields = capitalize_fields(ast.literal_eval(llm_output))
            extracted_dict = {field[0]: field[1] for field in extracted_fields}
            print(f"Campi estratti: {extracted_dict}")

            sparql_query = generate_sparql_query(extracted_dict)
            print(f"Query SPARQL generata:\n{sparql_query}")

            # Esegui la query SPARQL generata
            llm_sparql_results = execute_sparql_query(sparql_query)

            # Estrai URI dai risultati SPARQL
            uri_list = extract_uris(llm_sparql_results) if llm_sparql_results else []

            # Carica la mappatura URI -> ID dal file Excel
            uri_to_id_mapping = load_excel_mapping(EXCEL_FILE)

            # Mappa gli URI agli ID e ordina gli ID
            id_list = map_uris_to_ids(uri_list, uri_to_id_mapping)

            # Aggiorna l'oggetto con i risultati
            query_obj["llm_sparql"] = sparql_query
            query_obj["llm_results"] = id_list

            # Aggiungi l'oggetto aggiornato alla lista
            updated_data.append(query_obj)

        # Crea un nuovo nome per il file JSON
        new_file_path = os.path.join(json_folder, f"{os.path.splitext(filename)[0]}_LLM.json")

        # Salva il nuovo file JSON
        with open(new_file_path, 'w') as f:
            json.dump(updated_data, f, indent=4)

print("Elaborazione completata.")
