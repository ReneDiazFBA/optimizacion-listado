import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones ---
def extract_mining_title(title_string):
    if not isinstance(title_string, str):
        return "Título no encontrado"
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    if match:
        return match.group(1).strip()
    return "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)

        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=1)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=1)

        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None)
            title_string = mining_kw_raw.iloc[0, 0] if not mining_kw_raw.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=1)
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""

        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", header=0)
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer las pestañas. Error: {e}")
        st.session_state.datos_cargados = False

# --- App Principal ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    st.subheader("Tabla Consolidada de Search Terms (Cliente + Competencia + Mining)")

    # Preparar CustKW
    df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
    df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]

    # Preparar CompKW
    df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
    df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]

    # Preparar MiningKW
    df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
    df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']

    # Consolidar todo en una sola tabla
    df_all = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)

    # Consolidar duplicados por Search Terms
    df_consolidated = df_all.groupby('Search Terms').agg({
        'ASIN Click Share': 'first',
        'Sample Click Share': 'first',
        'Total Click Share': 'first',
        'Niche Click Share': 'first',
        'Sample Product Depth': 'first',
        'Niche Product Depth': 'first',
        'Relevance': 'first',
        'Search Volume': 'max',  # Usamos el volumen más alto disponible
    }).reset_index()

    # Formatear porcentajes
    percent_cols = ['ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share']
    for col in percent_cols:
        if col in df_consolidated.columns:
            df_consolidated[col] = pd.to_numeric(df_consolidated[col], errors='coerce') * 100
            df_consolidated[col] = df_consolidated[col].round(2).astype(str) + '%'

    st.metric("Total de Términos Consolidado", len(df_consolidated))
    st.dataframe(df_consolidated, height=500)
