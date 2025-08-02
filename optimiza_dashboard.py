import streamlit as st
import pandas as pd

st.title("Prueba de Lectura de Excel")

archivo = st.file_uploader("Sube tu archivo Excel para la prueba", type=["xlsx"])

if archivo:
    st.write("Archivo recibido. Intentando leer la pestaña 'CustKW'...")
    
    try:
        # Intentamos leer la pestaña específica que ha dado problemas
        df_test = pd.read_excel(archivo, sheet_name="CustKW", header=None)
        
        st.success("¡Éxito! La pestaña 'CustKW' se leyó correctamente.")
        
        st.write("Forma del dataframe (filas, columnas):", df_test.shape)
        
        st.write("Primeras 5 filas de la tabla:")
        st.dataframe(df_test.head())

    except Exception as e:
        st.error(f"Ocurrió un error al intentar leer la pestaña 'CustKW'.")
        st.exception(e)