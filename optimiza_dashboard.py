
import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones Auxiliares ---
# (Tu código original de funciones aquí... omitido por brevedad)
# ...

# --- Lógica Principal ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    
    # --- AQUI VAN TUS SECCIONES ORIGINALES ---
    # Datos del Cliente
    # Datos de Competidores
    # Datos de Mining
    # Datos de Avoids
    # (Todo exactamente como en tu código original...)

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
        
        column_order = [
            'Search Terms', 'Source', 'Search Volume', 
            'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share',
            'Sample Product Depth', 'Niche Product Depth', 'Relevance'
        ]
        existing_cols = [col for col in column_order if col in df_master.columns]
        df_master = df_master[existing_cols].fillna('N/A')

        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master, height=300)
