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

        # ---- INICIO DE LA CORRECCIÓN ----
        # Se lee la primera fila de la pestaña 'Avoids' como el encabezado (header=0).
        # Esto elimina la necesidad de asignar nombres de columna manualmente y evita duplicados.
        avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.avoids_df = avoids_df
        # ---- FIN DE LA CORRECCIÓN ----

        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", skiprows=1)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", skiprows=1)

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.session_state.datos_cargados = False

# El resto del código se omite por longitud, pero sería el mismo proporcionado en tu mensaje anterior.