import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimización de Listado", layout="wide")


# --- Funciones ---
def extract_mining_title(title_string):
    """Extrae el keyword principal del texto en la primera fila de la pestaña MiningKW."""
    if not isinstance(title_string, str):
        return "Título no encontrado"
    
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    if match:
        return match.group(1).strip()
    return "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        # Pestañas requeridas
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)

        # Se ajustan todas las tablas de keywords para usar la fila 2 como encabezado (header=1)
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=1)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=1)
        
        # Carga segura de pestañas opcionales
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
        st.error(f"Error al leer una de las pestañas. Asegúrate de que el archivo y las pestañas existan. Error: {e}")
        st.session_state.datos_cargados = False


def anadir_palabra_a_avoids(palabra, categoria):
    """Función para añadir una palabra a la categoría correcta en el dataframe de Avoids."""
    avoids_df = st.session_state.avoids_df
    last_idx = avoids_df[categoria].last_valid_index()
    target_idx = 0 if last_idx is None else last_idx + 1

    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)

    st.session_state.avoids_df.loc[target_idx, categoria] = palabra

def mostrar_pagina_categorizacion():
    """Muestra la interfaz para categorizar las palabras seleccionadas."""
    with st.container(border=True):
        st.subheader("Categorizar Palabras para Añadir a Avoids")
        st.write("Has seleccionado las siguientes palabras. Ahora, por favor, asigna una categoría a cada una.")
        
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
            
            submitted = st.form_submit_button("Confirmar y Añadir Palabras")
            if submitted:
                for palabra in palabras:
                    categoria = st.session_state[f"cat_{palabra}"]
                    anadir_palabra_a_avoids(palabra, categoria)
                
                st.success("¡Palabras añadidas a la lista de exclusión correctamente!")
                st.session_state.show_categorization_form = False
                del st.session_state.palabras_para_categorizar