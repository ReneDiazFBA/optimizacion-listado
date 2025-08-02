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
    """
    Carga los datos del Excel. Devuelve True si tiene éxito, False si falla,
    y muestra errores específicos en la interfaz.
    """
    try:
        xls = pd.ExcelFile(archivo_subido)
        
        # 1. Verificar que todas las pestañas obligatorias existan
        required_sheets = ["CustListing", "Avoids", "CustUnique", "CompUnique", "CustKW", "CompKW"]
        for sheet in required_sheets:
            if sheet not in xls.sheet_names:
                st.error(f"Error Crítico: No se encontró la pestaña obligatoria '{sheet}' en el archivo Excel.")
                return False

        # 2. Cargar pestañas simples
        st.session_state.df_asin = pd.read_excel(xls, sheet_name="CustListing")
        st.session_state.avoids_df = pd.read_excel(xls, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(xls, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(xls, sheet_name="CompUnique", header=0)

        # 3. Cargar y procesar hojas complejas con validación
        cust_kw_raw = pd.read_excel(xls, sheet_name="CustKW", header=None)
        if len(cust_kw_raw) < 3:
            st.error("Error de Formato: La pestaña 'CustKW' debe tener al menos 3 filas (info, encabezados, datos).")
            return False
        st.session_state.df_kw = cust_kw_raw.iloc[2:].copy()
        st.session_state.df_kw.columns = cust_kw_raw.iloc[1]

        comp_kw_raw = pd.read_excel(xls, sheet_name="CompKW", header=None)
        if len(comp_kw_raw) < 3:
            st.error("Error de Formato: La pestaña 'CompKW' debe tener al menos 3 filas.")
            return False
        st.session_state.comp_kw_raw = comp_kw_raw
        st.session_state.df_comp_data = comp_kw_raw.iloc[2:].copy()
        st.session_state.df_comp_data.columns = comp_kw_raw.iloc[1]
        
        # 4. Cargar pestañas opcionales
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(xls, sheet_name="MiningKW", header=None)
            if len(mining_kw_raw) > 2:
                title_string = mining_kw_raw.iloc[0, 0] if not mining_kw_raw.empty else ""
                st.session_state.mining_title = extract_mining_title(title_string)
                st.session_state.df_mining_kw = mining_kw_raw.iloc[2:].copy()
                st.session_state.df_mining_kw.columns = mining_kw_raw.iloc[1]
            else:
                st.session_state.df_mining_kw = pd.DataFrame()
                st.session_state.mining_title = ""
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""
        
        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(xls, sheet_name="MiningUnique", header=0)
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        return True  # Si todo sale bien, devuelve True
        
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar el archivo: {e}")
        return False # Si algo falla, devuelve False

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
            if st.form_submit_button("Confirmar y Añadir Palabras"):
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
        st.session_state.datos_cargados = inicializar_datos(archivo) # Actualiza el estado basado en el éxito de la carga

if st.session_state.get('datos_cargados', False):
    
    tab_cliente, tab_comp, tab_mining, tab_unicas, tab_maestra = st.tabs(["Datos del Cliente", "Datos de Competidores", "Minería de Keywords", "Palabras Únicas", "Tabla Maestra"])

    with tab_cliente:
        st.subheader("Listing de ASIN")
        for index, row in st.session_state.df_asin.iterrows():
            try:
                marketplace, asin, titulo, bullets, descripcion_raw = row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4]
                descripcion = "Este ASIN tiene contenido A+" if pd.isna(descripcion_raw) or str(descripcion_raw).strip() == "" else descripcion_raw
                with st.expander(f"ASIN: {asin}"):
                    st.markdown(f"**Marketplace:** {marketplace}\n\n**Titulo:** {titulo}\n\n**Bullet Points:** {bullets}\n\n**Descripción:** {descripcion}")
            except IndexError:
                st.warning(f"Se omitió la fila {index+1} de 'CustListing' por formato incorrecto.")
        
        st.subheader("Reverse ASIN del Producto")
        disable_filter_cliente = st.checkbox("Deshabilitar filtro", key="cliente_disable")
        opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
        seleccion_clicks = st.selectbox("ASIN Click Share >:", list(opciones_clicks.keys()), disabled=disable_filter_cliente)
        umbral_clicks = opciones_clicks[seleccion_clicks]
        
        df_kw_proc = st.session_state.df_kw.copy()
        columna_filtro_cliente = df_kw_proc.columns[1]
        
        if not disable_filter_cliente:
            df_kw_filtrado = df_kw_proc[pd.to_numeric(df_kw_proc[columna_filtro_cliente], errors='coerce').fillna(0) > umbral_clicks].copy()
        else:
            df_kw_filtrado = df_kw_proc.copy()

        st.metric("Total de Términos (Cliente)", len(df_kw_filtrado))
        st.dataframe(df_kw_filtrado)

    with tab_comp:
        st.subheader("ASIN de competidores")
        with st.expander("Ver/Ocultar ASINs de Competidores", expanded=True):
            df_comp_asins_raw = st.session_state.comp_kw_raw
            asin_raw = str(df_comp_asins_raw.iloc[0, 0])
            start_index = asin_raw.find('B0')
            clean_string_block = asin_raw[start_index:] if start_index != -1 else asin_raw
            clean_asin_list = [asin.split('-')[0].strip() for asin in clean_string_block.split(',') if asin.split('-')[0].strip()]
            st.dataframe(pd.DataFrame({"ASIN": clean_asin_list}))

        st.subheader("Reverse ASIN Competidores")
        disable_filter_competidores = st.checkbox("Deshabilitar filtro", key="comp_disable")
        rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1, disabled=disable_filter_competidores)
        
        df_comp_data_proc = st.session_state.df_comp_data.copy()
        columna_filtro_comp = df_comp_data_proc.columns[5]
        
        if not disable_filter_competidores:
            df_comp_data_proc[columna_filtro_comp] = pd.to_numeric(df_comp_data_proc[columna_filtro_comp], errors='coerce')
            df_comp_data_proc = df_comp_data_proc[df_comp_data_proc[columna_filtro_comp].notna() & (df_comp_data_proc[columna_filtro_comp] > rango)].copy()

        st.metric("Total de Términos (Competidores)", len(df_comp_data_proc))
        st.dataframe(df_comp_data_proc)

    with tab_mining:
        if not st.session_state.df_mining_kw.empty:
            st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
            disable_filter_mining = st.checkbox("Deshabilitar filtro", key="mining_disable")
            umbral_rel = st.selectbox("Relevance ≥:", [30, 50], disabled=disable_filter_mining)
            
            df_mining_proc = st.session_state.df_mining_kw.copy()
            columna_filtro_mining = df_mining_proc.columns[2]

            if not disable_filter_mining:
                df_mining_proc[columna_filtro_mining] = pd.to_numeric(df_mining_proc[columna_filtro_mining], errors='coerce').fillna(0)
                df_to_display = df_mining_proc[df_mining_proc[columna_filtro_mining] >= umbral_rel].copy()
            else:
                df_to_display = df_mining_proc.copy()

            st.metric("Total de Términos (Minería)", len(df_to_display))
            st.dataframe(df_to_display)
        else:
            st.info("No se encontró la pestaña 'MiningKW' en el archivo.")

    with tab_unicas:
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
                    st.success("Palabras eliminadas correctamente."); st.rerun()
                else:
                    st.warning("No has seleccionado ninguna palabra para eliminar.")

        st.subheader("Tabla Consolidada de Palabras Únicas")
        umbral_freq = st.selectbox("Frecuencia Mínima ≥:", [1, 2, 3, 4, 5], index=1)
        df_cust_u = st.session_state.df_cust_unique.iloc[:, [0, 1]].rename(columns={st.session_state.df_cust_unique.columns[0]: 'Keyword', st.session_state.df_cust_unique.columns[1]: 'Frec. Cliente'})
        df_comp_u = st.session_state.df_comp_unique.iloc[:, [0, 1]].rename(columns={st.session_state.df_comp_unique.columns[0]: 'Keyword', st.session_state.df_comp_unique.columns[1]: 'Frec. Comp.'})
        df_mining_u = st.session_state.df_mining_unique.iloc[:, [0, 1]].rename(columns={st.session_state.df_mining_unique.columns[0]: 'Keyword', st.session_state.df_mining_unique.columns[1]: 'Frec. Mining'})
        
        merged_df_u = pd.merge(df_cust_u, df_comp_u, on='Keyword', how='outer')
        final_df_u = pd.merge(merged_df_u, df_mining_u, on='Keyword', how='outer') if not df_mining_u.empty else merged_df_u.assign(**{'Frec. Mining': 0})
        
        freq_cols = ['Frec. Cliente', 'Frec. Comp.', 'Frec. Mining']
        for col in freq_cols:
            if col in final_df_u.columns:
                final_df_u[col] = pd.to_numeric(final_df_u[col], errors='coerce').fillna(0).astype(int)
        
        avoid_list = pd.concat([st.session_state.avoids_df[col] for col in st.session_state.avoids_df.columns]).dropna().unique().tolist()
        df_filtered_u = final_df_u[~final_df_u['Keyword'].isin(avoid_list)]
        df_filtered_u = df_filtered_u[df_filtered_u[freq_cols].ge(umbral_freq).any(axis=1)]
        
        if not df_filtered_u.empty:
            header_cols_spec = [0.5, 2, 1, 1, 1]
            header_cols = st.columns(header_cols_spec)
            header_cols[0].write("**Sel.**"); header_cols[1].write("**Keyword**"); header_cols[2].write("**Frec. Cliente**"); header_cols[3].write("**Frec. Comp.**"); header_cols[4].write("**Frec. Mining**")
            st.divider()
            for index, row in df_filtered_u.iterrows():
                row_cols = st.columns(header_cols_spec)
                row_cols[0].checkbox("", key=f"consolidada_cb_{index}")
                row_cols[1].write(row['Keyword']); row_cols[2].write(str(row['Frec. Cliente'])); row_cols[3].write(str(row['Frec. Comp.'])); row_cols[4].write(str(row['Frec. Mining']))
            st.divider()
            if st.button("añadir a Avoids", key="consolidada_add_to_avoids"):
                palabras_a_anadir = [row['Keyword'] for index, row in df_filtered_u.iterrows() if st.session_state.get(f"consolidada_cb_{index}")]
                if palabras_a_anadir:
                    st.session_state.palabras_para_categorizar = palabras_a_anadir
                    st.session_state.show_categorization_form = True; st.rerun()
                else:
                    st.warning("No has seleccionado ninguna palabra.")
        else:
            st.write("No hay palabras únicas para mostrar.")
    
    with tab_maestra:
        st.subheader("Tabla Maestra de Datos Compilados")
        df_cust = st.session_state.df_kw.copy().assign(Source='Cliente')
        df_comp = st.session_state.df_comp_data.copy().assign(Source='Competencia')
        df_mining = st.session_state.df_mining_kw.copy()
        if not df_mining.empty:
            df_mining['Source'] = 'Mining'
        
        df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)
        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master)