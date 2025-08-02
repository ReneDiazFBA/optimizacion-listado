
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
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)

        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=1)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=1)

        xls = pd.ExcelFile(archivo_subido)

        if 'MiningKW' in xls.sheet_names:
            title_df = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, nrows=1)
            title_string = title_df.iloc[0, 0] if not title_df.empty else ""
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
        st.error(f"Error al leer una de las pestañas. Error: {e}")
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
    st.success("Datos cargados correctamente")
    st.write("df_asin:", st.session_state.df_asin.shape)
    st.write("Avoids:", st.session_state.avoids_df.shape)
    st.write("CustKW:", st.session_state.df_kw.shape)
    st.write("CompKW:", st.session_state.df_comp_data.shape)
    if 'df_mining_kw' in st.session_state:
        st.write("MiningKW:", st.session_state.df_mining_kw.shape)
else:
    st.error("Los datos no fueron cargados correctamente.")
