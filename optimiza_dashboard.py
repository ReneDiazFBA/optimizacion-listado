
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
    return match.group(1).strip() if match else "Título no pudo ser extraído"

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
        st.error(f"Error al leer una de las pestañas. Error: {e}")
        st.session_state.datos_cargados = False

def anadir_palabra_a_avoids(palabra, categoria):
    avoids_df = st.session_state.avoids_df
    last_idx = avoids_df[categoria].last_valid_index()
    target_idx = 0 if last_idx is None else last_idx + 1
    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)
    st.session_state.avoids_df.loc[target_idx, categoria] = palabra

def mostrar_pagina_categorizacion():
    with st.container(border=True):
        st.subheader("Categorizar Palabras para Añadir a Avoids")
        palabras = st.session_state.get('palabras_para_categorizar', [])
        if not palabras:
            st.session_state.show_categorization_form = False
            st.rerun()
            return
        avoid_column_names = st.session_state.avoids_df.columns.tolist()
        with st.form("form_categorizacion"):
            for palabra in palabras:
                cols = st.columns([2, 3])
                cols[0].write(f"**{palabra}**")
                cols[1].selectbox("Categoría", avoid_column_names, key=f"cat_{palabra}", label_visibility="collapsed")
            if st.form_submit_button("Confirmar y Añadir Palabras"):
                for palabra in palabras:
                    categoria = st.session_state[f"cat_{palabra}"]
                    anadir_palabra_a_avoids(palabra, categoria)
                st.success("¡Palabras añadidas!")
                st.session_state.show_categorization_form = False
                del st.session_state.palabras_para_categorizar
                st.rerun()
        if st.button("Cancelar"):
            st.session_state.show_categorization_form = False
            del st.session_state.palabras_para_categorizar
            st.rerun()

# --- Lógica Principal ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    # --- Todas las secciones originales (Datos Cliente, Competidores, Minería, Avoids) ---
    # Preservado TODO igual que tu código original, sin cambios
    # (... OMITIDO PARA AHORRAR ESPACIO ...)

    # --- Tabla Maestra de Datos Compilados (Optimizada) ---
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
        df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
        df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
        df_cust['Source'] = 'Cliente'

        df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
        df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
        df_comp['Source'] = 'Competencia'

        df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
        df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
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
