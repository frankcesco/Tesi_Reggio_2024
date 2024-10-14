import pandas as pd
import ast
import pickle
from tqdm import tqdm
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
import re
import json
import itertools

# Carica il file Excel in un DataFrame
df = pd.read_excel('../all_products.xlsx', sheet_name='all_products', engine='openpyxl')

# Funzione per rimuovere i tag HTML
def remove_html_tags(html_content):
    if isinstance(html_content, str):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ').strip()
    return html_content

# Applica la funzione alla colonna delle descrizioni
df['post_content'] = df['post_content'].apply(remove_html_tags)

# Salva il DataFrame modificato in un nuovo file Excel
df.to_excel('../prodotti_puliti.xlsx', index=False, engine='openpyxl')
print("Descrizioni pulite salvate in 'prodotti_puliti.xlsx'")

# Definizione del sistema di classificazione
system = '''
<variabile>
{descrizione}
</variabile>

<contesto>
Sei un frontend developer e stai lavorando a un e-commerce. Il tuo compito è classificare i prodotti in in modo dicotomico (0-1). La variabile {descrizione} contiene la descrizione di un prodotto. Classifica i prodotti in base alla loro descrizione nelle seguenti categorie: 
1) Agrumato
2) Ambrato
3) Aromatico
4) Chypre
5) Cuoio
6) Dolce
7) Floreale
8) Fruttato
7) Gourmand
8) Legnoso
9) Muschiato
10) Senza Profumo
11) Speziato Leggero
</contesto>

<istruzioni>
1. Leggi la {descrizione} del prodotto.
2. Per ogni categoria assegna un punteggio 0 oppure 1 in base alla presenza o assenza di elementi caratteristici.
3. Esegui l'output in formato list di python, come indicato nel tag <output>.
</istruzioni>

<output>
[ ["Agrumato", punteggio], ["Ambrato", punteggio], ["Aromatico", punteggio], ["Chypre", punteggio], ["Cuoio", punteggio], ["Dolce", punteggio], ["Floreale", punteggio], ["Fruttato", punteggio], ["Gourmand", punteggio], ["Legnoso", punteggio], ["Muschiato", punteggio], ["Senza Profumo", punteggio], ["Speziato Leggero", punteggio] ]
</output>
'''

chat = ChatGroq(temperature=0.5, model_name="llama3-groq-70b-8192-tool-use-preview", groq_api_key='example_api_key')

prompt = ChatPromptTemplate(
    input_variables=['descrizione'],
    messages=[
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=['descrizione'], template=system)
        )
    ]
)

chain = prompt | chat

# CATEGORIZZATORE
with open("cat.pickle", "rb") as file:
    cat = pickle.load(file)

start = len(cat)

for i in tqdm(range(2801, len(df['post_content']))):
    description = df['post_content'][i]
    success = False
    t = 0
    while not success:
        try:
            testo = chain.invoke(description)
            testo = testo.content
            cat.append(testo)
            success = True
        except Exception as e:
            error_message = str(e)
            if 'context_length_exceeded' in error_message:
                description = description[:300]
                print(f"Context length exceeded per i={i}. Ridotto a 300 caratteri.")
                t = 0
            elif 'internal_server_error' in error_message:
                print(f"Errore del server interno per i={i}. Riprovando con lo stesso testo.")
                time.sleep(1)
            else:
                print(f"Errore generale (i={i}, tentativo={t+1}): {e}")
                t += 1
                if t >= 10:
                    print(f"Numero massimo di tentativi raggiunto per i={i}. Aggiungo valore di fallback.")
                    cat.append([["Agrumato", 0], ["Ambrato", 0], ["Aromatico", 0], ["Chypre", 0], ["Cuoio", 0], ["Dolce", 0], ["Floreale", 0], ["Fruttato", 0], ["Gourmand", 0], ["Legnoso", 0], ["Muschiato", 0], ["Senza Profumo", 0], ["Speziato Leggero", 0]])
                    success = True
                else:
                    time.sleep(1)

# CORREGGE FORMATTAZIONE
with open("cat_serializzato.pickle", "rb") as file:
    cat = pickle.load(file)

system_formattazione = '''
<variabile>
{lista}
</variabile>

<contesto>
Sei un developer e devi verificare che la formattazione di una lista di liste sia corretta. La variabile {lista} contiene una lista di coppie di valori, in cui il primo elemento è una stringa e il secondo è un intero. Verifica che la lista sia correttamente formattata e correggila se necessario.
</contesto>

<istruzioni>
1. Leggi la {lista}, in formato lista di Python.
2. Verifica che la lista sia correttamente formattata, ovvero che ogni elemento sia una lista di due elementi: una stringa e un intero booleano (0 o 1). La lista deve essere aperta e chiusa da parentesi quadre, e ogni elemento deve essere separato da una virgola.
3. Formatta la lista come in <output>.
</istruzioni>

<output>
[ ["Agrumato", punteggio], ["Ambrato", punteggio], ["Aromatico", punteggio], ["Chypre", punteggio], ["Cuoio", punteggio], ["Dolce", punteggio], ["Floreale", punteggio], ["Fruttato", punteggio], ["Gourmand", punteggio], ["Legnoso", punteggio], ["Muschiato", punteggio], ["Senza Profumo", punteggio], ["Speziato Leggero", punteggio] ]
</output>
'''

prompt_formattazione = ChatPromptTemplate(
    input_variables=['lista'],
    messages=[
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=['lista'], template=system_formattazione)
        )
    ]
)

llm_chain = LLMChain(llm=chat, prompt=prompt_formattazione)

def correggi_formattazione(elemento, index):
    tentativi = 0
    while tentativi < 100:
        try:
            testo_corretto = llm_chain.run({"lista": elemento})
            corretto = ast.literal_eval(testo_corretto.strip())
            if isinstance(corretto, list) and all(
                isinstance(elem, list) and len(elem) == 2 and isinstance(elem[0], str) and isinstance(elem[1], int)
                for elem in corretto
            ):
                return testo_corretto
        except Exception as e:
            print(f"Errore durante la correzione della formattazione per l'indice {index}: {e}")
        tentativi += 1

    return str([["Agrumato", 0], ["Ambrato", 0], ["Aromatico", 0], ["Chypre", 0], ["Cuoio", 0], ["Dolce", 0], ["Floreale", 0], ["Fruttato", 0], ["Gourmand", 0], ["Legnoso", 0], ["Muschiato", 0], ["Senza Profumo", 0], ["Speziato Leggero", 0]])

def verifica_formattazione(elemento):
    try:
        lista = ast.literal_eval(elemento)
        if isinstance(lista, list) and all(
            isinstance(item, list) and len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], int)
        ):
            return True
    except (SyntaxError, ValueError):
        return False
    return False

elementi_malfatti = []
for idx, i in enumerate(tqdm(cat)):
    if not verifica_formattazione(i):
        elementi_malfatti.append(idx)

with open("elementi_malfatti_serializzato.pickle", "wb") as file:
    pickle.dump(elementi_malfatti, file)

if elementi_malfatti:
    for idx in tqdm(elementi_malfatti):
        cat[idx] = correggi_formattazione(cat[idx], idx)
        with open("cat_serializzato.pickle", "wb") as file:
            pickle.dump(cat, file)

print("Tutti gli elementi malformati sono stati corretti con successo!")

# ESPORTA IN XLSX
def converti_in_lista_di_liste(elemento):
    try:
        lista = ast.literal_eval(elemento)
        if isinstance(lista, list):
            return lista
    except (SyntaxError, ValueError):
        pass
    return None

df['categorie'] = pd.Series(cat).apply(converti_in_lista_di_liste)

df.to_excel("../prodotti_classificati_finale.xlsx", index=False, engine='openpyxl')

print("Classificazioni salvate con successo in 'prodotti_classificati_finale.xlsx'")
