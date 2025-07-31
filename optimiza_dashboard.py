import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")


# --- Funciones ---
def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)
        st.session_state.datos_cargados = True
        st.session_state.vista_actual = 'dashboard' # Vista inicial
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.session_state.datos_cargados = False

def mostrar_dashboard():
    """Muestra la interfaz principal de la aplicación."""
    st.title("Optimización de Listado - Dashboard")
    
    # DATOS DEL CLIENTE
    with st.expander("Datos del cliente", expanded=False):
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"], key="cliente_radio")
        if subtabs == "Listado de ASINs":
            # (Código de esta sección sin cambios)
            for _, row in st.session_state.df_asin.iterrows():
                asin = row.get("ASIN", "")
                titulo = row.get("Product Title", "")
                bullets = row.get("Bullet Points", "")
                descripcion = row.get("Description", "")
                with st.expander(f"ASIN: {asin}"):
                    st.markdown("**Título del producto:**")
                    st.write(titulo)
                    st.markdown("**Puntos clave:**")
                    st.write(bullets)
                    if pd.notna(descripcion) and str(descripcion).strip():
                        st.markdown("**Descripción:**")
                        st.write(descripcion)
        elif subtabs == "Palabras Clave (Keywords)":
            opciones = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion = st.selectbox("Filtrar por porcentaje de clics:", list(opciones.keys()))
            umbral = opciones[seleccion]
            df_kw_copy = st.session_state.df_kw.copy()
            df_kw_copy["Click Share"] = pd.to_numeric(df_kw_copy["Click Share"], errors="coerce")
            df_kw_filtrado = df_kw_copy[df_kw_copy["Click Share"].fillna(0) > umbral]
            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)
            columnas = ["Keyword", "M. Searches", "Click Share"]
            with st.expander("Ver/Ocultar Keywords del Cliente", expanded=True):
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
                st.dataframe(df_kw_filtrado[columnas].reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
                st.markdown("</div>", unsafe_allow_html=True)

    # DATOS DE COMPETIDORES
    with st.expander("Datos de competidores", expanded=False):
        # (Código de esta sección sin cambios)
        st.subheader("ASIN de competidores")
        with st.expander("Ver/Ocultar ASINs de Competidores", expanded=True):
            asin_raw = str(st.session_state.df_comp.iloc[0, 0])
            if "ExpandKeywords" in asin_raw:
                cuerpo = asin_raw.replace("ExpandKeywords(439)-US-", "").split("-Last-30-days")[0]
                asin_list = [a.strip() for a in cuerpo.split(",") if a.strip()]
                df_asin_comp = pd.DataFrame({"ASIN de competidor": asin_list})
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
                st.dataframe(df_asin_comp.style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
                st.markdown("</div>", unsafe_allow_html=True)
        st.subheader("Keywords por ranking de competidor")
        rango = st.selectbox("Mostrar keywords con ranking mayor a:", [4, 5, 6], index=1)
        df_comp_data_copy = st.session_state.df_comp_data.copy()
        df_comp_data_copy.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
        cols = df_comp_data_copy.iloc[:, [0, 5, 8, 18]].copy()
        cols.columns = ["Palabra clave", "Ranking ASIN", "Impresiones", "CTR"]
        cols = cols.dropna()
        cols['Ranking ASIN'] = pd.to_numeric(cols['Ranking ASIN'], errors='coerce')
        cols = cols[cols["Ranking ASIN"].notna() & (cols["Ranking ASIN"] > rango)]
        with st.expander("Ver/Ocultar Keywords de Competidores por Ranking", expanded=True):
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(cols.reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
            st.markdown("</div>", unsafe_allow_html=True)

    # SECCIÓN DE PALABRAS ÚNICAS
    with st.expander("Palabras Únicas", expanded=True): # Lo dejo expandido por defecto
        
        st.subheader("Agregar nuevas palabras a Avoids")
        avoid_column_names = st.session_state.avoids_df.columns.tolist()
        with st.form(key="avoid_form"):
            nueva_palabra = st.text_input("Escribe una palabra nueva:")
            categoria_seleccionada = st.selectbox("Categoría", avoid_column_names)
            submitted = st.form_submit_button("Agregar a Avoids")

            if submitted and nueva_palabra:
                avoids_df = st.session_state.avoids_df
                last_idx = avoids_df[categoria_seleccionada].last_valid_index()
                target_idx = 0 if last_idx is None else last_idx + 1

                if target_idx >= len(avoids_df):
                    new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
                    st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)

                st.session_state.avoids_df.loc[target_idx, categoria_seleccionada] = nueva_palabra
                st.success(f"Palabra '{nueva_palabra}' agregada a '{categoria_seleccionada}'.")
                st.experimental_rerun()


        st.subheader("Palabras en lista de exclusión ('Avoids')")
        with st.expander("Ver/Ocultar Listas de Exclusión", expanded=True):
            col1, col2, col3 = st.columns(3)
            avoids_display = st.session_state.avoids_df
            col1_name, col2_name, col3_name = avoid_column_names[0], avoid_column_names[1], avoid_column_names[2]

            with col1:
                st.dataframe(avoids_display[col1_name].dropna().reset_index(drop=True), use_container_width=True)
            with col2:
                st.dataframe(avoids_display[col2_name].dropna().reset_index(drop=True), use_container_width=True)
            with col3:
                st.dataframe(avoids_display[col3_name].dropna().reset_index(drop=True), use_container_width=True)

        avoid_list = pd.concat([st.session_state.avoids_df[col] for col in avoid_column_names]).dropna().unique().tolist()
        st.divider()

        # --- PALABRAS ÚNICAS DEL CLIENTE ---
        st.subheader("Palabras únicas del cliente (filtradas)")
        filtro_cust = st.checkbox("Ocultar frecuencia ≤ 2", value=True, key="fc")
        
        with st.expander("Ver/Ocultar Palabras del Cliente", expanded=True):
            df_cust = st.session_state.df_cust_unique
            df_cust_filtered = df_cust[~df_cust[df_cust.columns[0]].isin(avoid_list)]
            if filtro_cust and len(df_cust.columns) > 1:
                freq_col_cust = df_cust.columns[1]
                df_cust_filtered[freq_col_cust] = pd.to_numeric(df_cust_filtered[freq_col_cust], errors='coerce')
                df_cust_filtered = df_cust_filtered[df_cust_filtered[freq_col_cust].notna() & (df_cust_filtered[freq_col_cust] > 2)]

            if not df_cust_filtered.empty:
                header_cols_spec = [0.5, 2] + [1] * (len(df_cust_filtered.columns) - 1)
                header_cols = st.columns(header_cols_spec)
                header_cols[0].write("**Sel.**")
                for i, col_name in enumerate(df_cust_filtered.columns):
                    header_cols[i+1].write(f"**{col_name}**")
                
                st.divider()

                for index, row in df_cust_filtered.iterrows():
                    row_cols = st.columns(header_cols_spec)
                    row_cols[0].checkbox("", key=f"cust_cb_{index}")
                    for i, col_name in enumerate(df_cust_filtered.columns):
                        row_cols[i+1].write(row[col_name])
                
                st.divider()
                if st.button("añadir a Avoids", key="cust_add_to_avoids"):
                    palabras_a_anadir = []
                    for index, row in df_cust_filtered.iterrows():
                        if st.session_state.get(f"cust_cb_{index}"):
                            palabra = row[df_cust_filtered.columns[0]]
                            palabras_a_anadir.append(palabra)
                    
                    if palabras_a_anadir:
                        st.session_state.palabras_para_categorizar = palabras_a_anadir
                        st.session_state.vista_actual = 'categorizar'
                        st.experimental_rerun()
                    else:
                        st.warning("No has seleccionado ninguna palabra.")
            else:
                st.write("No hay datos de palabras únicas del cliente para mostrar.")
        
        # --- PALABRAS ÚNICAS DE COMPETIDORES ---
        st.subheader("Palabras únicas de competidores (filtradas)")
        filtro_comp = st.checkbox("Ocultar frecuencia ≤ 2 (competidores)", value=True, key="fc2")

        with st.expander("Ver/Ocultar Palabras de Competidores", expanded=True):
            df_comp = st.session_state.df_comp_unique
            df_comp_filtered = df_comp[~df_comp[df_comp.columns[0]].isin(avoid_list)]
            if filtro_comp and len(df_comp.columns) > 1:
                freq_col_comp = df_comp.columns[1]
                df_comp_filtered[freq_col_comp] = pd.to_numeric(df_comp_filtered[freq_col_comp], errors='coerce')
                df_comp_filtered = df_comp_filtered[df_comp_filtered[freq_col_comp].notna() & (df_comp_filtered[freq_col_comp] > 2)]

            if not df_comp_filtered.empty:
                header_cols_spec_comp = [0.5, 2] + [1] * (len(df_comp_filtered.columns) - 1)
                header_cols_comp = st.columns(header_cols_spec_comp)
                header_cols_comp[0].write("**Sel.**")
                for i, col_name in enumerate(df_comp_filtered.columns):
                    header_cols_comp[i+1].write(f"**{col_name}**")

                st.divider()

                for index, row in df_comp_filtered.iterrows():
                    row_cols_comp = st.columns(header_cols_spec_comp)
                    row_cols_comp[0].checkbox("", key=f"comp_cb_{index}")
                    for i, col_name in enumerate(df_comp_filtered.columns):
                        row_cols_comp[i+1].write(row[col_name])
                
                st.divider()
                if st.button("añadir a Avoids", key="comp_add_to_avoids"):
                    palabras_a_anadir_comp = []
                    for index, row in df_comp_filtered.iterrows():
                        if st.session_state.get(f"comp_cb_{index}"):
                            palabra = row[df_comp_filtered.columns[0]]
                            palabras_a_anadir_comp.append(palabra)
                            
                    if palabras_a_anadir_comp:
                        st.session_state.palabras_para_categorizar = palabras_a_anadir_comp
                        st.session_state.vista_actual = 'categorizar'
                        st.experimental_rerun()
                    else:
                        st.warning("No has seleccionado ninguna palabra.")
            else:
                st.write("No hay datos de palabras únicas de competidores para mostrar.")

def mostrar_pagina_categorizacion():
    """Muestra la interfaz para categorizar las palabras seleccionadas."""
    st.title("Categorizar Palabras para Añadir a Avoids")
    st.write("Has seleccionado las siguientes palabras. Ahora, por favor, asigna una categoría a cada una.")
    
    palabras = st.session_state.get('palabras_para_categorizar', [])
    if not palabras:
        st.warning("No hay palabras para categorizar. Volviendo al dashboard...")
        st.session_state.vista_actual = 'dashboard'
        st.experimental_rerun()
        return

    st.write(f"Palabras seleccionadas: **{', '.join(palabras)}**")
    
    # Placeholder para la siguiente funcionalidad
    st.info("El siguiente paso será agregar los menús desplegables y el botón de confirmación aquí.")

    if st.button("Cancelar y Volver"):
        st.session_state.vista_actual = 'dashboard'
        del st.session_state.palabras_para_categorizar
        st.experimental_rerun()

# --- Lógica Principal de la App ---
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    if st.session_state.get('vista_actual', 'dashboard') == 'dashboard':
        mostrar_dashboard()
    else:
        mostrar_pagina_categorizacion()