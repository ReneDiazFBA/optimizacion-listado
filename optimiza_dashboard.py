
import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones Auxiliares ---
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
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=1)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=1)
        
        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            title_df = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, nrows=1, engine='openpyxl')
            title_string = title_df.iloc[0, 0] if not title_df.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=1, engine='openpyxl')
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""
        
        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", header=0)
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer las pestañas: {e}")
        st.session_state.datos_cargados = False

# --- Lógica Principal de la App ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
        cust_kw_raw = pd.read_excel(archivo, sheet_name="CustKW", header=None)
        comp_kw_raw = pd.read_excel(archivo, sheet_name="CompKW", header=None)
        mining_kw_raw = pd.read_excel(archivo, sheet_name="MiningKW", header=None) if 'MiningKW' in pd.ExcelFile(archivo).sheet_names else pd.DataFrame()

        df_cust = cust_kw_raw.iloc[2:].copy()
        df_cust.columns = cust_kw_raw.iloc[1]
        df_cust = df_cust.iloc[:, [0, 1, 15, 25]]
        df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
        df_cust['Source'] = 'Cliente'

        df_comp = comp_kw_raw.iloc[2:].copy()
        df_comp.columns = comp_kw_raw.iloc[1]
        df_comp = df_comp.iloc[:, [0, 2, 5, 8, 18]]
        df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
        df_comp['Source'] = 'Competencia'

        if not mining_kw_raw.empty:
            df_mining = mining_kw_raw.iloc[2:].copy()
            df_mining.columns = mining_kw_raw.iloc[1]
            df_mining = df_mining.iloc[:, [0, 2, 5, 12, 15]]
            df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
            df_mining['Source'] = 'Mining'
        else:
            df_mining = pd.DataFrame()

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
        
        column_order = [
            'Search Terms', 'Source', 'Search Volume', 
            'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share',
            'Sample Product Depth', 'Niche Product Depth', 'Relevance'
        ]
        existing_cols = [col for col in column_order if col in df_master.columns]
        df_master = df_master[existing_cols].fillna('N/A')

        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master, height=300)
