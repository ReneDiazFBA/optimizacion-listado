
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        avoids = pd.read_excel(archivo, sheet_name="Avoids")
        df_cust_unique = pd.read_excel(archivo, sheet_name="CustUnique")
        df_comp_unique = pd.read_excel(archivo, sheet_name="CompUnique")
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
    df_cust = df_cust_unique.rename(columns=lambda c: c.strip().capitalize())
    if filtro:
        df_cust = df_cust[df_cust["Frequency"] > 2]
    st.data_editor(df_cust.reset_index(drop=True), key="cust_unique", use_container_width=True)

    st.subheader("Palabras únicas de competidores")
    filtro2 = st.checkbox("Ocultar palabras con frecuencia ≤ 2 (competidores)", value=True)
    df_comp = df_comp_unique.rename(columns=lambda c: c.strip().capitalize())
    if filtro2:
        df_comp = df_comp[df_comp["Frequency"] > 2]
    st.data_editor(df_comp.reset_index(drop=True), key="comp_unique", use_container_width=True)

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
