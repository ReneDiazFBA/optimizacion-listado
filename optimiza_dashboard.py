
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Optimización de Listado", layout="wide")

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
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=None, skiprows=2)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None, skiprows=2)
        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None)
            title_string = mining_kw_raw.iloc[0, 0] if not mining_kw_raw.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, skiprows=2)
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

st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

    if st.session_state.get('datos_cargados', False):
        tabs = st.tabs(["Cliente", "Competidores", "Minería", "Palabras Únicas"])

        with tabs[0]:
            st.subheader("Datos del Cliente")
            st.dataframe(st.session_state.df_asin)
            disable_filter_cliente = st.checkbox("Deshabilitar filtro Cliente")
            st.subheader("Reverse ASIN del Producto")
            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
            df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')
            if not disable_filter_cliente:
                df_kw_proc = df_kw_proc[df_kw_proc["ASIN Click Share"] > 0.05]
            df_kw_proc["ASIN Click Share"] = (df_kw_proc["ASIN Click Share"] * 100).round(2).astype(str) + "%"
            st.dataframe(df_kw_proc.reset_index(drop=True), height=400)

        with tabs[1]:
            st.subheader("ASINs de Competidores")
            df_comp_header = pd.read_excel(archivo, sheet_name="CompKW", header=None)
            asin_raw = str(df_comp_header.iloc[0, 0])
            asin_list = [a.split('-')[0].strip() for a in asin_raw.split(',') if a.startswith('B0')]
            st.dataframe(pd.DataFrame({"ASIN": asin_list}))
            disable_filter_comp = st.checkbox("Deshabilitar filtro Competidores")
            st.subheader("Reverse ASIN Competidores")
            df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_data_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
            df_comp_data_proc['Sample Click Share'] = pd.to_numeric(df_comp_data_proc['Sample Click Share'], errors='coerce')
            if not disable_filter_comp:
                df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Sample Product Depth"] > 5]
            df_comp_data_proc['Sample Click Share'] = (df_comp_data_proc['Sample Click Share'] * 100).round(2).astype(str) + '%'
            st.dataframe(df_comp_data_proc.reset_index(drop=True), height=400)

        with tabs[2]:
            st.subheader("Minería de Search Terms")
            disable_filter_mining = st.checkbox("Deshabilitar filtro Minería")
            if not st.session_state.df_mining_kw.empty:
                df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
                df_mining_proc.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
                df_mining_proc['Relevance'] = pd.to_numeric(df_mining_proc['Relevance'], errors='coerce')
                if not disable_filter_mining:
                    df_mining_proc = df_mining_proc[df_mining_proc['Relevance'] >= 30]
                st.dataframe(df_mining_proc.reset_index(drop=True), height=400)
            else:
                st.write("No hay datos de minería disponibles.")

        with tabs[3]:
            st.subheader("Palabras Únicas (Avoids)")
            st.dataframe(st.session_state.avoids_df)

        st.subheader("Tabla Maestra de Datos Compilados")
        st.write("Aquí unirías las tablas CustKW, CompKW y MiningKW como ya lo tienes estructurado.")
else:
    st.warning("Por favor, sube un archivo Excel para comenzar.")
