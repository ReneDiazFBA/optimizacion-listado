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
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Se restauró el contenido de las siguientes dos secciones
    
    # DATOS DEL CLIENTE
    with st.expander("Datos del cliente", expanded=False):
        st.subheader("Listado de ASINs")
        for index, row in st.session_state.df_asin.iterrows():
            try:
                marketplace = row.iloc[0]
                asin = row.iloc[1]
                titulo = row.iloc[2]
                bullets = row.iloc[3]
                descripcion_raw = row.iloc[4]

                if pd.isna(descripcion_raw) or str(descripcion_raw).strip() == "":
                    descripcion = "Este ASIN tiene contenido A+"
                else:
                    descripcion = descripcion_raw

                with st.expander(f"ASIN: {asin}"):
                    st.markdown(f"**Marketplace:** {marketplace}")
                    st.markdown("**Título del producto:**")
                    st.write(titulo)
                    st.markdown("**Puntos clave:**")
                    st.write(bullets)
                    st.markdown("**Descripción:**")
                    st.write(descripcion)
            except IndexError:
                st.warning(f"Se omitió la fila {index+1} de la pestaña 'CustListing' por no tener el formato esperado.")
                continue
        
        st.divider()

        st.subheader("Palabras Clave (Keywords)")
        opciones = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
        seleccion = st.selectbox("Filtrar por porcentaje de clics:", list(opciones.keys()))
        umbral = opciones[seleccion]
        
        df_kw_copy = st.session_state.df_kw.iloc[:, [0, 1, 15]].copy()
        df_kw_copy.columns = ["Keyword", "Click Share", "M. Searches"]

        df_kw_copy["Click Share"] = pd.to_numeric(df_kw_copy["Click Share"], errors="coerce")
        df_kw_filtrado = df_kw_copy[df_kw_copy["Click Share"].fillna(0) > umbral]
        df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
        df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)
        
        columnas_a_mostrar = ["Keyword", "M. Searches", "Click Share"]
        
        with st.expander("Ver/Ocultar Keywords del Cliente", expanded=True):
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_kw_filtrado[columnas_a_mostrar].reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
            st.markdown("</div>", unsafe_allow_html=True)

    # DATOS DE COMPETIDORES
    with st.expander("Datos de competidores", expanded=False):
        st.subheader("ASIN de competidores")
        with st.expander("Ver/Ocultar ASINs de Competidores", expanded=True):
            asin_raw = str(st.session_state.df_comp.iloc[0, 0])
            
            start_index = asin_raw.find('B0')
            if start_index != -1:
                clean_string_block = asin_raw[start_index:]
            else:
                clean_string_block = asin_raw

            dirty_asin_list = clean_string_block.split(',')
            
            clean_asin_list = []
            for asin in dirty_asin_list:
                clean_asin = asin.split('-')[0].strip()
                if clean_asin:
                    clean_asin_list.append(clean_asin)

            df_asin_comp = pd.DataFrame({"ASIN de competidor": clean_asin_list})
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_asin_comp.style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Keywords por ranking de competidor")
        rango = st.selectbox("Mostrar keywords con ranking mayor a:", [4, 5, 6], index=1)
        df_comp_data_copy = st.session_state.df_comp_data.copy()
        df_comp_data_copy.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
        cols = df_comp_data_copy.iloc[:, [0, 5, 8, 18]].copy()
        
        cols.columns = ["Palabra clave", "Cmp. Depth", "Impresiones", "Click Share"]
        cols = cols.dropna()
        
        cols['Impresiones'] = pd.to_numeric(cols['Impresiones'], errors='coerce').fillna(0).astype(int)
        cols['Click Share'] = pd.to_numeric(cols['Click Share'], errors='coerce').fillna(0)
        cols['Click Share'] = cols['Click Share'].round(2).astype(str) + '%'
        cols['Cmp. Depth'] = pd.to_numeric(cols['Cmp. Depth'], errors='coerce')
        cols = cols[cols["Cmp. Depth"].notna() & (cols["Cmp. Depth"] > rango)]

        with st.expander("Ver/Ocultar Keywords de Competidores por Ranking", expanded=True):
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(cols.reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
            st.markdown("</div>", unsafe_allow_html=True)

    # --- FIN DE LA CORRECCIÓN ---

    # DATOS DE MINERÍA (Solo se mostrará si la pestaña existe en el Excel)
    if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
        with st.expander("Minería de Datos", expanded=False):
            
            st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
            st.divider()

            df_mining = st.session_state.df_mining_kw
            
            try:
                col_a_name = df_mining.columns[0]
                col_c_name = df_mining.columns[2]
                col_f_name = df_mining.columns[5]

                df_to_display = df_mining[[col_a_name, col_f_name, col_c_name]].copy()
                df_to_display.columns = ['Keywords', 'Búsquedas Mensuales', 'Relevancia']
                
                st.dataframe(df_to_display)

            except (IndexError, KeyError) as e:
                st.error(f"El formato de la pestaña 'MiningKW' no es el esperado. No se pudieron encontrar las columnas A, C o F. Error: {e}")

    # SECCIÓN DE PALABRAS ÚNICAS
    with st.expander("Palabras Únicas", expanded=True): 
        
        if st.session_state.get('show_categorization_form', False):
            mostrar_pagina_categorizacion()
            st.divider()

        st.subheader("Palabras en lista de exclusión ('Avoids')")
        with st.expander("Ver/Ocultar Listas de Exclusión", expanded=True):
            col1, col2, col3 = st.columns(3)
            avoids_df = st.session_state.avoids_df
            avoid_column_names = avoids_df.columns.tolist()
            
            col_map = {col1: avoid_column_names[0], col2: avoid_column_names[1], col3: avoid_column_names[2]}

            for col_widget, col_name in col_map.items():
                with col_widget:
                    st.markdown(f"**{col_name}**")
                    for index, word in avoids_df[col_name].dropna().items():
                        st.checkbox(label=str(word), key=f"del_avoid_{col_name}_{index}")
            
            st.divider()
            if st.button("Eliminar seleccionados de la lista", key="delete_avoids"):
                palabras_eliminadas = False
                for col_name in avoid_column_names:
                    for index, word in avoids_df[col_name].dropna().items():
                        if st.session_state.get(f"del_avoid_{col_name}_{index}"):
                            st.session_state.avoids_df.loc[index, col_name] = pd.NA
                            palabras_eliminadas = True
                
                if palabras_eliminadas:
                    st.success("Palabras eliminadas correctamente.")
                    st.rerun()
                else:
                    st.warning("No has seleccionado ninguna palabra para eliminar.")

        avoid_list = pd.concat([st.session_state.avoids_df[col] for col in st.session_state.avoids_df.columns]).dropna().unique().tolist()
        st.divider()

        st.subheader("Tabla Consolidada de Palabras Únicas")

        df_cust = st.session_state.df_cust_unique.iloc[:, [0, 1]].copy()
        df_cust.columns = ['Keyword', 'Frec. Cliente']

        df_comp = st.session_state.df_comp_unique.iloc[:, [0, 1]].copy()
        df_comp.columns = ['Keyword', 'Frec. Comp.']
        
        df_mining = st.session_state.df_mining_unique.iloc[:, [0, 1]].copy()
        df_mining.columns = ['Keyword', 'Frec. Mining']

        merged_df = pd.merge(df_cust, df_comp, on='Keyword', how='outer')
        if not df_mining.empty:
            final_df = pd.merge(merged_df, df_mining, on='Keyword', how='outer')
        else:
            final_df = merged_df
            final_df['Frec. Mining'] = 0

        freq_cols = ['Frec. Cliente', 'Frec. Comp.', 'Frec. Mining']
        for col in freq_cols:
            if col in final_df.columns:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)

        df_filtered = final_df[~final_df['Keyword'].isin(avoid_list)]

        filtro_freq = st.checkbox("Ocultar si todas las frecuencias son ≤ 2", value=True, key="freq_consolidada")
        if filtro_freq:
            df_filtered = df_filtered[df_filtered[freq_cols].gt(2).any(axis=1)]

        if not df_filtered.empty:
            header_cols_spec = [0.5, 2, 1, 1, 1]
            header_cols = st.columns(header_cols_spec)
            header_cols[0].write("**Sel.**")
            header_cols[1].write("**Keyword**")
            header_cols[2].write("**Frec. Cliente**")
            header_cols[3].write("**Frec. Comp.**")
            header_cols[4].write("**Frec. Mining**")
            st.divider()

            for index, row in df_filtered.iterrows():
                row_cols = st.columns(header_cols_spec)
                row_cols[0].checkbox("", key=f"consolidada_cb_{index}")
                row_cols[1].write(row['Keyword'])
                row_cols[2].write(str(row['Frec. Cliente']))
                row_cols[3].write(str(row['Frec. Comp.']))
                row_cols[4].write(str(row['Frec. Mining']))

            st.divider()

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