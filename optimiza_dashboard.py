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
    
    # DATOS DEL CLIENTE
    with st.expander("Datos del cliente", expanded=False):
        # ... (código sin cambios)
    
    # DATOS DE COMPETIDORES
    with st.expander("Datos de competidores", expanded=False):
        # ... (código sin cambios)

    # DATOS DE MINERÍA (Solo se mostrará si la pestaña existe en el Excel)
    if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
        with st.expander("Minería de Datos", expanded=False):
            # ... (código sin cambios)
            
    # SECCIÓN DE PALABRAS ÚNICAS
    with st.expander("Palabras Únicas", expanded=True): 
        
        if st.session_state.get('show_categorization_form', False):
            mostrar_pagina_categorizacion()
            st.divider()

        st.subheader("Palabras en lista de exclusión ('Avoids')")
        with st.expander("Ver/Ocultar Listas de Exclusión", expanded=True):
            # ... (código sin cambios)

        avoid_list = pd.concat([st.session_state.avoids_df[col] for col in st.session_state.avoids_df.columns]).dropna().unique().tolist()
        st.divider()

        # --- INICIO DE LA NUEVA TABLA CONSOLIDADA ---
        st.subheader("Tabla Consolidada de Palabras Únicas")

        # Preparar dataframes individuales
        df_cust = st.session_state.df_cust_unique.iloc[:, [0, 1]].copy()
        df_cust.columns = ['Keyword', 'Frec. Cliente']

        df_comp = st.session_state.df_comp_unique.iloc[:, [0, 1]].copy()
        df_comp.columns = ['Keyword', 'Frec. Comp.']
        
        df_mining = st.session_state.df_mining_unique.iloc[:, [0, 1]].copy()
        df_mining.columns = ['Keyword', 'Frec. Mining']

        # Unir los dataframes
        merged_df = pd.merge(df_cust, df_comp, on='Keyword', how='outer')
        if not df_mining.empty:
            final_df = pd.merge(merged_df, df_mining, on='Keyword', how='outer')
        else:
            final_df = merged_df
            final_df['Frec. Mining'] = 0 # Añadir columna si no existe

        # Limpiar y formatear
        freq_cols = ['Frec. Cliente', 'Frec. Comp.', 'Frec. Mining']
        for col in freq_cols:
            if col in final_df.columns:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)

        # Filtrar por lista de avoids
        df_filtered = final_df[~final_df['Keyword'].isin(avoid_list)]

        # Filtro de frecuencia
        filtro_freq = st.checkbox("Ocultar si todas las frecuencias son ≤ 2", value=True, key="freq_consolidada")
        if filtro_freq:
            # Mantener la fila si CUALQUIER columna de frecuencia es > 2
            df_filtered = df_filtered[df_filtered[freq_cols].gt(2).any(axis=1)]

        # Mostrar tabla interactiva
        if not df_filtered.empty:
            # Encabezados
            header_cols_spec = [0.5, 2, 1, 1, 1]
            header_cols = st.columns(header_cols_spec)
            header_cols[0].write("**Sel.**")
            header_cols[1].write("**Keyword**")
            header_cols[2].write("**Frec. Cliente**")
            header_cols[3].write("**Frec. Comp.**")
            header_cols[4].write("**Frec. Mining**")
            st.divider()

            # Filas con checkboxes
            for index, row in df_filtered.iterrows():
                row_cols = st.columns(header_cols_spec)
                # Usamos el índice original del dataframe para una clave única
                row_cols[0].checkbox("", key=f"consolidada_cb_{index}")
                row_cols[1].write(row['Keyword'])
                row_cols[2].write(str(row['Frec. Cliente']))
                row_cols[3].write(str(row['Frec. Comp.']))
                row_cols[4].write(str(row['Frec. Mining']))

            st.divider()

            # Botón para añadir a Avoids
            if st.button("añadir a Avoids", key="consolidada_add_to_avoids"):
                palabras_a_anadir = []
                for index, row in df_filtered.iterrows():
                    if st.session_state.get(f"consolidada_cb_{index}"):
                        palabras_a_anadir.append(row['Keyword'])
                
                if palabras_a_anadir:
                    st.session_state.palabras_para_categorizar = palabras_a_anadir
                    st.session_state.show_categorization_form = True
                    st.rerun()
                else:
                    st.warning("No has seleccionado ninguna palabra.")
        else:
            st.write("No hay palabras únicas para mostrar con los filtros actuales.")
        # --- FIN DE LA NUEVA TABLA CONSOLIDADA ---