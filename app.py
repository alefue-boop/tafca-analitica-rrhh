import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Control de Tratos - Tafca SPA", layout="wide")
st.title("Consolidador y Dashboard de Tratos en Obra")

st.info("Sube los reportes de asistencia (CSV) descargados de cada unidad de negocio para generar el reporte.")

# Crear 3 espacios para subir los archivos
col_arch1, col_arch2, col_arch3 = st.columns(3)

with col_arch1:
    file_239 = st.file_uploader("1. Archivo UN 239", type=['csv'])
with col_arch2:
    file_234 = st.file_uploader("2. Archivo UN 234 (AALL Rengo)", type=['csv'])
with col_arch3:
    file_227 = st.file_uploader("3. Archivo UN 227 (Marimaura)", type=['csv'])

# Solo ejecutar el código si los 3 archivos han sido subidos
if file_239 and file_234 and file_227:
    try:
        columnas_maestras = [
            'Faena', 'RUT', 'Nombre', 'Cargo', 'Centro_Costo', 
            'Monto_Tratos', 'Monto_DT', 'Bonos', 'Gasto_Total', 'Descripcion'
        ]

        # --- PROCESAMIENTO ---
        # UN 239
        df_239 = pd.read_csv(file_239, skiprows=2)
        df_239 = df_239.rename(columns={'NOMBRE': 'Nombre', 'CARGO': 'Cargo', 'EQ. A CARGO': 'Centro_Costo', 'Total Horas Trato': 'Monto_Tratos', 'Valor a Pagar': 'Monto_DT', 'BONOS': 'Bonos', 'SUMA  TOTAL': 'Gasto_Total', 'DESCRIPCION DE': 'Descripcion'})
        df_239 = df_239.reindex(columns=columnas_maestras)

        # UN 234
        df_234 = pd.read_csv(file_234, skiprows=3)
        df_234 = df_234.rename(columns={'NOMBRE': 'Nombre', 'CARGO': 'Cargo', 'GRUPO TRABAJO': 'Centro_Costo', 'Sub Total': 'Monto_Tratos', 'Sub Total.1': 'Monto_DT', 'Bonos': 'Bonos', 'TRATOS': 'Gasto_Total', 'LOS BONOS PAGADOS': 'Descripcion'})
        df_234 = df_234.reindex(columns=columnas_maestras)

        # UN 227
        df_227 = pd.read_csv(file_227, skiprows=3)
        df_227 = df_227.rename(columns={'NOMBRE': 'Nombre', 'CARGO': 'Cargo', 'GRUPO TRABAJO': 'Centro_Costo', 'Sub Total': 'Monto_Tratos', 'Sub Total.1': 'Monto_DT', 'Otros': 'Bonos', 'TOTAL': 'Gasto_Total', 'DESCRIPCION DE': 'Descripcion'})
        df_227 = df_227.reindex(columns=columnas_maestras)

        # --- UNIFICACIÓN ---
        df_maestro = pd.concat([df_239, df_234, df_227], ignore_index=True)
        df_maestro = df_maestro.dropna(subset=['RUT'])
        
        columnas_montos = ['Monto_Tratos', 'Monto_DT', 'Bonos', 'Gasto_Total']
        for col in columnas_montos:
            df_maestro[col] = pd.to_numeric(df_maestro[col], errors='coerce').fillna(0)
        
        df_maestro = df_maestro[df_maestro['Gasto_Total'] > 0]
        df_maestro['Descripcion'] = df_maestro['Descripcion'].fillna('Sin descripción')
        df_maestro.insert(0, 'Periodo', '2026-03')

        st.success("¡Datos procesados y unificados correctamente!")
        st.divider()

        # --- VISUALIZACIÓN DEL DASHBOARD ---
        gasto_total = df_maestro['Gasto_Total'].sum()
        total_trabajadores = df_maestro['RUT'].nunique()
        
        st.subheader("Resumen General de Gasto")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Gasto Total en Tratos", f"${gasto_total:,.0f}")
        kpi2.metric("Trabajadores Involucrados", total_trabajadores)
        kpi3.metric("Promedio por Trabajador", f"${(gasto_total/total_trabajadores):,.0f}")
        
        st.divider()

        col_graf, col_datos = st.columns([1, 1.5])
        
        with col_graf:
            st.write("### Gasto por Faena")
            gasto_faena = df_maestro.groupby('Faena')['Gasto_Total'].sum().reset_index()
            st.bar_chart(gasto_faena, x='Faena', y='Gasto_Total')
            
        with col_datos:
            st.write("### Base de Datos Consolidada")
            st.dataframe(df_maestro[['Faena', 'RUT', 'Nombre', 'Cargo', 'Gasto_Total']], use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error procesando las columnas. Verifica que los archivos correspondan a cada unidad: {e}")
