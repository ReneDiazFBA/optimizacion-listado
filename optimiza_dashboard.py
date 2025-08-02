
import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

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
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", usecols=['A', 'B'], skiprows=1)
        st.session_state.df_cust_unique.columns = ['Keyword', 'Frec. Cliente']
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", usecols=['A', 'B'], skiprows=1)
        st.session_state.df_comp_unique.columns = ['Keyword', 'Frec. Comp.']

        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", usecols=['A', 'B', 'P', 'Z'], skiprows=2)
        st.session_state.df_kw.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]

        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", usecols=['A', 'C', 'F', 'I', 'S'], skiprows=2)
        st.session_state.df_comp_data.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]

        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            title_df = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, nrows=1)
            title_string = title_df.iloc[0, 0] if not title_df.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", usecols=['A', 'C', 'F', 'M', 'P'], skiprows=2)
            st.session_state.df_mining_kw.columns = ["Search Terms", "Relevance", "Search Volume", "Niche Product Depth", "Niche Click Share"]
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""

        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", usecols=['A', 'B'], skiprows=1)
            st.session_state.df_mining_unique.columns = ['Keyword', 'Frec. Mining']
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer una de las pestañas. Asegúrate de que el archivo y las pestañas existan. Error: {e}")
        st.session_state.datos_cargados = False

# --- Lógica Principal ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
        df_cust = st.session_state.df_kw.copy()
        df_cust['Source'] = 'Cliente'

        df_comp = st.session_state.df_comp_data.copy()
        df_comp['Source'] = 'Competencia'

        df_mining = st.session_state.df_mining_kw.copy()
        df_mining['Source'] = 'Mining'

        df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)

        numeric_cols = ['Search Volume', 'ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share', 'Sample Product Depth', 'Niche Product Depth', 'Relevance']
        for col in numeric_cols:
            if col in df_master.columns:
                df_master[col] = pd.to_numeric(df_master[col], errors='coerce')

        percent_cols = ['ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share']
        for col in percent_cols:
            if col in df_master.columns:
                mask = df_master[col].notna()
                df_master.loc[mask, col] = (df_master.loc[mask, col] * 100).round(2).astype(str) + '%'

        column_order = ['Search Terms', 'Source', 'Search Volume', 'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share', 'Sample Product Depth', 'Niche Product Depth', 'Relevance']
        existing_cols = [col for col in column_order if col in df_master.columns]
        df_master = df_master[existing_cols].fillna('N/A')

        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master, height=300)
