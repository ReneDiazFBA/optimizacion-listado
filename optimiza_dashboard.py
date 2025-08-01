import streamlit as st
import pandas as pd
import re

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
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)

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
                st.rerun()

        if st.button("Cancelar"):
            st.session_state.show_categorization_form = False
            del st.session_state.palabras_para_categorizar
            st.rerun()

# --- Lógica Principal de la App ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    
    with st.expander("Análisis de Volumen de Búsqueda", expanded=True):
        st.subheader("Tabla Maestra de Keywords y Volumen de Búsqueda")

        # 1. Extraer y estandarizar datos (sigue siendo necesario para los cálculos)
        df_cust_sv = st.session_state.df_kw.iloc[:, [0, 15]].copy()
        df_cust_sv.columns = ['Keyword', 'Volumen Cliente']

        df_comp_sv = st.session_state.df_comp_data.iloc[:, [0, 8]].copy()
        df_comp_sv.columns = ['Keyword', 'Volumen Competidor']
        
        df_mining_sv = st.session_state.df_mining_kw.iloc[:, [0, 5]].copy()
        df_mining_sv.columns = ['Keyword', 'Volumen Mining']

        merged_df = pd.merge(df_cust_sv, df_comp_sv, on='Keyword', how='outer')
        final_df = pd.merge(merged_df, df_mining_sv, on='Keyword', how='outer')

        sv_cols = ['Volumen Cliente', 'Volumen Competidor', 'Volumen Mining']
        for col in sv_cols:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)

        final_df['Volumen (Más Alto)'] = final_df[sv_cols].max(axis=1)
        
        # --- INICIO DE LA CORRECCIÓN ---
        
        # 2. Crear filtros y ordenamiento
        col_f, col_s = st.columns(2)
        with col_f:
            opciones_volumen = ['No mostrar Ceros', 'Mostrar Solo Ceros', '>= 300', '>= 500', '>= 700', '>= 1000']
            seleccion_volumen = st.selectbox("Filtrar por volumen:", opciones_volumen)
        
        with col_s:
            opciones_sort = ['Volumen (Descendente)', 'Volumen (Ascendente)', 'Keyword (A-Z)', 'Keyword (Z-A)']
            seleccion_sort = st.selectbox("Ordenar por:", opciones_sort)
            
        # 3. Aplicar filtro de volumen
        df_filtrado = final_df.copy()
        if seleccion_volumen == 'No mostrar Ceros':
            df_filtrado = final_df[final_df['Volumen (Más Alto)'] > 0]
        elif seleccion_volumen == 'Mostrar Solo Ceros':
            df_filtrado = final_df[final_df['Volumen (Más Alto)'] == 0]
        else:
            umbral = int(seleccion_volumen.replace('>= ', ''))
            df_filtrado = final_df[final_df['Volumen (Más Alto)'] >= umbral]

        # 4. Aplicar ordenamiento
        if seleccion_sort == 'Volumen (Descendente)':
            df_ordenado = df_filtrado.sort_values(by='Volumen (Más Alto)', ascending=False)
        elif seleccion_sort == 'Volumen (Ascendente)':
            df_ordenado = df_filtrado.sort_values(by='Volumen (Más Alto)', ascending=True)
        elif seleccion_sort == 'Keyword (A-Z)':
            df_ordenado = df_filtrado.sort_values(by='Keyword', ascending=True)
        else: # Keyword (Z-A)
            df_ordenado = df_filtrado.sort_values(by='Keyword', ascending=False)
            
        # 5. Seleccionar solo las columnas finales para mostrar
        result_df = df_ordenado[['Keyword', 'Volumen (Más Alto)']]
        
        st.dataframe(result_df.reset_index(drop=True))
        # --- FIN DE LA CORRECCIÓN ---


    with st.expander("Datos para Análisis", expanded=False):

        # DATOS DEL CLIENTE
        with st.expander("Datos del cliente", expanded=False):
            # ... (código sin cambios)

        # DATOS DE COMPETIDORES
        with st.expander("Datos de competidores", expanded=False):
            # ... (código sin cambios)

        # DATOS DE MINERÍA
        if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
            with st.expander("Minería de Datos", expanded=False):
                # ... (código sin cambios)

        # SECCIÓN DE PALABRAS ÚNICAS
        with st.expander("Palabras Únicas", expanded=True): 
            # ... (código sin cambios)