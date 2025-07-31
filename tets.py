import streamlit as st
import pandas as pd

st.title("Prueba de Diagnóstico para Excel")
st.write("Sube tu archivo para ver cómo lo lee el programa con dos configuraciones diferentes.")

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        st.divider()
        # --- PRUEBA 1 ---
        st.header("Prueba A: `header=0`")
        st.write("""
        Esta prueba asume que la **primera fila** de tu hoja `CustUnique` contiene los títulos 
        ('Word', 'Frequency', etc.).
        """)
        df_test_A = pd.read_excel(archivo, sheet_name="CustUnique", header=0)
        st.write("**Resultado de la Prueba A:**")
        st.dataframe(df_test_A.head())

        st.divider()

        # --- PRUEBA 2 ---
        st.header("Prueba B: `header=1`")
        st.write("""
        Esta prueba asume que la **primera fila** es un título general que se ignora, 
        y que los verdaderos títulos están en la **segunda fila**.
        """)
        df_test_B = pd.read_excel(archivo, sheet_name="CustUnique", header=1)
        st.write("**Resultado de la Prueba B:**")
        st.dataframe(df_test_B.head())

    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo. Esto puede pasar si la pestaña 'CustUnique' no existe o está vacía. Error: {e}")