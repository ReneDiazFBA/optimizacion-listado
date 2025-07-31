
import streamlit as st
import pandas as pd
from collections import Counter

# Lista simple de stopwords en inglés para filtrar
stop_words = {
    "the", "for", "and", "with", "are", "but", "from", "was", "that", "this", "these", "those", "there", "their",
    "have", "has", "had", "not", "will", "would", "can", "could", "should", "shall", "may", "might", "to", "in",
    "on", "at", "of", "by", "an", "a", "as", "is", "it", "be", "been", "or", "if", "we", "you", "your", "our", 
    "they", "them", "he", "she", "his", "her", "its", "do", "does", "did", "so", "than"
}

def procesar_keywords(df, stoplist):
    words = []
    for phrase in df.iloc[:, 0].dropna():
        for word in str(phrase).lower().split():
            clean = word.strip(".,:;!?()[]{}\"'")
            if clean and clean not in stoplist:
                words.append(clean)
    conteo = pd.DataFrame(Counter(words).items(), columns=["Palabra", "Frecuencia"])
    return conteo.sort_values(by="Frecuencia", ascending=False)

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        avoids = pd.read_excel(archivo, sheet_name="Avoids")
        cust_unique = pd.read_excel(archivo, sheet_name="CustUnique")
        comp_unique = pd.read_excel(archivo, sheet_name="CompUnique")
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.stop()

    st.subheader("Palabras en lista de exclusión ('Avoids')")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Stopwords**")
    col1.dataframe(avoids.iloc[:, 0].dropna().reset_index(drop=True))
    col2.markdown("**Marcas**")
    col2.dataframe(avoids.iloc[:, 1].dropna().reset_index(drop=True))
    col3.markdown("**Irrelevantes**")
    col3.dataframe(avoids.iloc[:, 2].dropna().reset_index(drop=True))

    st.markdown("---")
    st.subheader("Palabras únicas del cliente")
    filtro = st.checkbox("Ocultar palabras con frecuencia ≤ 2", value=True)
    tabla_cust = procesar_keywords(cust_unique, stop_words)
    if filtro:
        tabla_cust = tabla_cust[tabla_cust["Frecuencia"] > 2]
    selected_rows = st.data_editor(tabla_cust, num_rows="dynamic", use_container_width=True)

    st.subheader("Palabras únicas de competidores")
    filtro2 = st.checkbox("Ocultar palabras con frecuencia ≤ 2 (competidores)", value=True)
    tabla_comp = procesar_keywords(comp_unique, stop_words)
    if filtro2:
        tabla_comp = tabla_comp[tabla_comp["Frecuencia"] > 2]
    selected_rows2 = st.data_editor(tabla_comp, num_rows="dynamic", use_container_width=True)

    st.markdown("---")
    st.subheader("Agregar nuevas palabras a Avoids")

    nueva_palabra = st.text_input("Escribe una palabra nueva:")
    categoria = st.selectbox("Categoría", ["Stopword", "Marca", "Irrelevante"])
    if st.button("Agregar a lista temporal"):
        if "nuevas_avoids" not in st.session_state:
            st.session_state["nuevas_avoids"] = []
        st.session_state["nuevas_avoids"].append((nueva_palabra.strip(), categoria))

    if "nuevas_avoids" in st.session_state and st.session_state["nuevas_avoids"]:
        st.markdown("### Palabras nuevas seleccionadas:")
        df_nuevas = pd.DataFrame(st.session_state["nuevas_avoids"], columns=["Palabra", "Categoría"])
        st.dataframe(df_nuevas, use_container_width=True)
