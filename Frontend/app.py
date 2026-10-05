import streamlit as st

st.title("Hola Mundo")
nombre = st.text_input("Nombre")
if nombre:
    st.write(f"Hola {nombre}")