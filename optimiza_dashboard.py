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

        # CustKW
        cust_kw_raw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=None)
        st.session_state.df_kw = cust_kw_raw.iloc[3:].copy()
        st.session_state.df_kw.columns = cust_kw_raw.iloc[1]

        # CompKW
        comp_kw_raw = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = comp_kw_raw.iloc[3:].copy()
        st.session_state.df_comp_data.columns = comp_kw_raw.iloc[1]

        # MiningKW
        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None)
            title_string = mining_kw_raw.iloc[0, 0] if not mining_kw_raw.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = mining_kw_raw.iloc[3:].copy()
            st.session_state.df_mining_kw.columns = mining_kw_raw.iloc[1]
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
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
