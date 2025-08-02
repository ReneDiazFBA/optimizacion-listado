
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")

def inicializar_datos(archivo_subido):
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)

        cust_kw_raw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=None, skiprows=2)
        cust_kw_raw.columns = ["Search Terms", "ASIN Click Share"] + [f"Col_{i}" for i in range(3, 16)] + ["Search Volume"] + [f"Col_{i}" for i in range(17, 25)] + ["Total Click Share"]
        st.session_state.df_kw = cust_kw_raw

        comp_kw_raw = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None, skiprows=2)
        comp_kw_raw.columns = ["Search Terms", "Col_B", "Sample Click Share", "Col_D", "Col_E", "Sample Product Depth", "Col_G", "Col_H", "Search Volume"] + [f"Col_{i}" for i in range(10, 18)] + ["Niche Click Share"]
        st.session_state.df_comp_data = comp_kw_raw

        mining_kw_raw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, skiprows=2)
        mining_kw_raw.columns = ["Search Terms"] + [f"Col_{i}" for i in range(1, 2)] + ["Relevance"] + [f"Col_{i}" for i in range(3, 5)] + ["Search Volume"] + [f"Col_{i}" for i in range(6, 12)] + ["Niche Product Depth"] + [f"Col_{i}" for i in range(13, 15)] + ["Niche Click Share"]
        st.session_state.df_mining_kw = mining_kw_raw

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.session_state.datos_cargados = False

st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    with st.expander("Datos para Análisis", expanded=True):
        st.subheader("Datos del Cliente")
        st.dataframe(st.session_state.df_asin)
        
        st.subheader("Datos de Competidores")
        st.dataframe(st.session_state.df_comp_data)
        
        st.subheader("Datos de Minería")
        st.dataframe(st.session_state.df_mining_kw)
        
        st.subheader("Lista de Exclusión (Avoids)")
        st.dataframe(st.session_state.avoids_df)

    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
        df_cust = st.session_state.df_kw[["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]].copy()
        df_cust["Source"] = "Cliente"

        df_comp = st.session_state.df_comp_data[["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]].copy()
        df_comp["Source"] = "Competencia"

        df_mining = st.session_state.df_mining_kw[["Search Terms", "Relevance", "Search Volume", "Niche Product Depth", "Niche Click Share"]].copy()
        df_mining["Source"] = "Mining"

        df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)
        st.dataframe(df_master)
