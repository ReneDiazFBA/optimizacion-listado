import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

# --- Funciones Auxiliares ---
def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)

        # Lee la primera fila de la pestaña 'Avoids' como el encabezado.
        avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.avoids_df = avoids_df

        # ---- INICIO DE LA CORRECCIÓN ----
        # Se especifica que el encabezado está en la PRIMERA fila del Excel (índice 0).
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)
        # ---- FIN DE LA CORRECCIÓN ----

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.session_state.datos_cargados = False

# --- Interfaz de Usuario ---
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

# Reinicia el estado si se sube un nuevo archivo.
if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name

    if not st.session_state.get('datos_cargados', False):
        inicializar_datos(archivo)

# Muestra el dashboard solo si los datos han sido cargados exitosamente.
if st.session_state.get('datos_cargados', False):

    # DATOS DEL CLIENTE
    with st.expander("Datos del cliente", expanded=False):
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"], key="cliente_radio")

        if subtabs == "Listado de ASINs":
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
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_kw_filtrado[columnas].reset_index(drop=True).style.set_properties(**{
                "white-space": "normal", "word-wrap": "break-word"
            }))
            st.markdown("</div>", unsafe_allow_html=True)

    # DATOS DE COMPETIDORES
    with st.expander("Datos de competidores", expanded=False):
        st.subheader("ASIN de competidores")
        asin_raw = str(st.session_state.df_comp.iloc[0, 0])
        if "ExpandKeywords" in asin_raw:
            cuerpo = asin_raw.replace("ExpandKeywords(439)-US-", "").split("-Last-30-days")[0]
            asin_list = [a.strip() for a in cuerpo.split(",") if a.strip()]
            df_asin_comp = pd.DataFrame({"ASIN de competidor": asin_list})
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_asin_comp.style.set_properties(**{
                "white-space": "normal", "word-wrap": "break-word"
            }))
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
        st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
        st.dataframe(cols.reset_index(drop=True).style.set_properties(**{
            "white-space": "normal", "word-wrap": "break-word"
        }))
        st.markdown("</div>", unsafe_allow_html=True)

    # SECCIÓN PARA AGREGAR Y MOSTRAR AVOIDS
    st.subheader("Agregar nuevas palabras a Avoids")

    avoid_column_names = st.session_state.avoids_df.columns.tolist()

    with st.form(key="avoid_form"):
        nueva_palabra = st.text_input("Escribe una palabra nueva:")
        categoria = st.selectbox("Categoría", avoid_column_names)
        submitted = st.form_submit_button("Agregar a Avoids")

        if submitted and nueva_palabra:
            avoids_df = st.session_state.avoids_df
            last_idx = avoids_df[categoria].last_valid_index()
            target_idx = 0 if last_idx is None else last_idx + 1

            if target_idx >= len(avoids_df):
                new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
                st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)

            st.session_state.avoids_df.loc[target_idx, categoria] = nueva_palabra
            st.success(f"Palabra '{nueva_palabra}' agregada a '{categoria}'. Las tablas de palabras únicas se han actualizado.")

    st.subheader("Palabras en lista de exclusión ('Avoids')")
    col1, col2, col3 = st.columns(3)

    avoids_display = st.session_state.avoids_df
    col1_name, col2_name, col3_name = avoid_column_names[0], avoid_column_names[1], avoid_column_names[2]

    with col1:
        st.dataframe(avoids_display[col1_name].dropna().reset_index(drop=True), use_container_width=True)
    with col2:
        st.dataframe(avoids_display[col2_name].dropna().reset_index(drop=True), use_container_width=True)
    with col3:
        st.dataframe(avoids_display[col3_name].dropna().reset_index(drop=True), use_container_width=True)


    # LÓGICA DE FILTRADO Y VISUALIZACIÓN DE PALABRAS ÚNICAS
    avoid_list = pd.concat([
        avoids_display[col] for col in avoid_column_names
    ]).dropna().unique().tolist()

    st.subheader("Palabras únicas del cliente (filtradas)")
    filtro_cust = st.checkbox("Ocultar frecuencia ≤ 2", value=True, key="fc")

    df_cust = st.session_state.df_cust_unique
    
    if not df_cust.empty:
        word_column_cust = df_cust.columns[0]
        freq_column_cust = df_cust.columns[1] if len(df_cust.columns) > 1 else None

        df_cust_filtered = df_cust[~df_cust[word_column_cust].isin(avoid_list)]

        if filtro_cust and freq_column_cust:
            df_cust_filtered[freq_column_cust] = pd.to_numeric(df_cust_filtered[freq_column_cust], errors='coerce')
            df_cust_filtered = df_cust_filtered[df_cust_filtered[freq_column_cust].notna() & (df_cust_filtered[freq_column_cust] > 2)]
    else:
        df_cust_filtered = df_cust

    st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
    st.dataframe(df_cust_filtered.reset_index(drop=True).style.set_properties(**{
        "white-space": "normal", "word-wrap": "break-word"
    }))
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Palabras únicas de competidores (filtradas)")
    filtro_comp = st.checkbox("Ocultar frecuencia ≤ 2 (competidores)", value=True, key="fc2")

    df_comp = st.session_state.df_comp_unique

    if not df_comp.empty:
        word_column_comp = df_comp.columns[0]
        freq_column_comp = df_comp.columns[1] if len(df_comp.columns) > 1 else None

        df_comp_filtered = df_comp[~df_comp[word_column_comp].isin(avoid_list)]

        if filtro_comp and freq_column_comp:
            df_comp_filtered[freq_column_comp] = pd.to_numeric(df_comp_filtered[freq_column_comp], errors='coerce')
            df_comp_filtered = df_comp_filtered[df_comp_filtered[freq_column_comp].notna() & (df_comp_filtered[freq_column_comp] > 2)]
    else:
        df_comp_filtered = df_comp

    st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
    st.dataframe(df_comp_filtered.reset_index(drop=True).style.set_properties(**{
        "white-space": "normal", "word-wrap": "break-word"
    }))
    st.markdown("</div>", unsafe_allow_html=True)