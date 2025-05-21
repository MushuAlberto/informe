import streamlit as st
import pandas as pd
from datetime import date

# --- Configuración inicial ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.datos_principales = {}
    st.session_state.tabla_empresas = pd.DataFrame({
        'Empresas Transportistas': [
            "MSD Bateas", "M&Q Bateas", "M&Q Aljibes",
            "Coseducam Bateas", "Coseducam Aljibes", "Jorquera Aljibes",
            "Ramplas AG Services", "Ramplas MSD", "Ramplas Coseducam",
            "", "Totales"
        ],
        'Prog.': [0]*11,
        'Real': [0]*11
    })
    st.session_state.tabla_operacional = pd.DataFrame({
        'Concepto': [
            "Sector",
            "Producto",
            "Destino",
            "Despacho Tonelaje",
            "% Cumplimiento",
            "Equipos General",
            "M&Q Aljibes",
            "Coseducam Aljibes",
            "Jorquera Aljibes",
            "% Regulaciones",
            "Promedio de Carga",
            "Tiempo Interior Faena"
        ],
        'Programado': [''] * 12,
        'Real': [''] * 12
    })

# Opciones para selector de producto (fila 2)
productos_opciones = [
    "BISCHOFITA", "MOP 70", "MOP TALCO", "MOP TALCO MAXIS", "MOP-G",
    "MOP-G (Rojo)", "MOP-G 59", "MOP-G O", "MOP-G PLUS", "MOP-G R 59",
    "MOP-GR PLUS", "MOP-H-AL", "MOP-H-BL", "MOP-S", "MOP-S 59",
    "MOP-S PLUS", "NACL", "SAL 27/15", "SILVINITA", "SLIT",
    "SOP-G", "SOP-H", "SOP-O", "SOP-S Talco", "USOP52",
    "MOP 50", "SOP FINO", "LSI (S)"
]

# Opciones para selector de sector (fila 1)
sectores_opciones = ["MOP-I", "MOP-II", "POZAS"]

# Funciones auxiliares
def tiempo_a_minutos(tiempo_str):
    try:
        horas, minutos = map(int, tiempo_str.split(':'))
        return horas * 60 + minutos
    except:
        return None

def minutos_a_tiempo(minutos):
    return f"{minutos//60:02d}:{minutos%60:02d}"

# Interfaz principal
st.title("Sistema de Registro Operacional")

# Paso 1: Datos principales
if st.session_state.step == 1:
    st.header("📝 Paso 1: Datos Principales")

    with st.form("form_principal"):
        fecha = st.date_input("Fecha", value=date.today())
        abc_seguridad = st.selectbox("ABC de Seguridad", ["A", "B", "C"])
        tiempo_salar = st.text_input("Tiempo Salar de Atacama (HH:MM)", "00:00")
        tiempo_pto = st.text_input("Tiempo Pto. Angamos (HH:MM)", "00:00")

        if st.form_submit_button("Siguiente →"):
            tiempo_salar_min = tiempo_a_minutos(tiempo_salar)
            tiempo_pto_min = tiempo_a_minutos(tiempo_pto)

            if None in [tiempo_salar_min, tiempo_pto_min]:
                st.error("⚠️ Formato de tiempo incorrecto. Use HH:MM")
            else:
                st.session_state.datos_principales = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'abc_seguridad': abc_seguridad,
                    'tiempo_salar': tiempo_salar_min,
                    'tiempo_pto': tiempo_pto_min
                }
                st.session_state.step = 2
                st.rerun()

# Paso 2: Tabla de empresas
elif st.session_state.step == 2:
    st.header("🏭 Paso 2: Empresas Transportistas")
    st.write("Ingrese los valores programados y reales:")

    df = st.session_state.tabla_empresas

    for i in range(len(df)-1):
        if df.loc[i, 'Empresas Transportistas']:
            cols = st.columns([4, 2, 2])
            with cols[0]:
                st.write(df.loc[i, 'Empresas Transportistas'])
            with cols[1]:
                df.at[i, 'Prog.'] = st.number_input(
                    "Prog.", min_value=0, value=int(df.loc[i, 'Prog.']),
                    key=f"prog_{i}", label_visibility="collapsed"
                )
            with cols[2]:
                df.at[i, 'Real'] = st.number_input(
                    "Real", min_value=0, value=int(df.loc[i, 'Real']),
                    key=f"real_{i}", label_visibility="collapsed"
                )

    total_prog = df.loc[:8, 'Prog.'].sum()
    total_real = df.loc[:8, 'Real'].sum()

    st.markdown("---")
    cols = st.columns([4, 2, 2])
    with cols[0]:
        st.markdown("**Totales**")
    with cols[1]:
        st.markdown(f"**{total_prog}**")
    with cols[2]:
        st.markdown(f"**{total_real}**")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Volver"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Siguiente →"):
            st.session_state.step = 3
            st.rerun()

# Paso 3: Tabla operacional con filas fijas
elif st.session_state.step == 3:
    st.header("📊 Paso 3: Datos Operacionales por Sector")

    df_op = st.session_state.tabla_operacional
    nombres_filas = df_op['Concepto'].tolist()

    st.write("Complete los valores programados y reales para cada indicador:")

    for i in range(12):
        cols = st.columns([3, 2, 2])
        with cols[0]:
            st.markdown(f"**{nombres_filas[i]}**")
        # Fila 1: Selector de sector
        if i == 0:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.selectbox(
                    "Sector",
                    sectores_opciones,
                    index=sectores_opciones.index(df_op.at[i, 'Programado']) if df_op.at[i, 'Programado'] in sectores_opciones else 0,
                    key=f"sector_{i}",
                    label_visibility="collapsed"
                )
        # Fila 2: Selector de producto
        elif i == 1:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.selectbox(
                    "Producto",
                    productos_opciones,
                    index=productos_opciones.index(df_op.at[i, 'Programado']) if df_op.at[i, 'Programado'] in productos_opciones else 0,
                    key=f"producto_{i}",
                    label_visibility="collapsed"
                )
        # Otras filas: Campos de texto
        else:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.text_input(
                    f"Prog. {i+1}",
                    value=df_op.at[i, 'Programado'],
                    key=f"prog_op_{i}",
                    label_visibility="collapsed"
                )
        with cols[2]:
            df_op.at[i, 'Real'] = st.text_input(
                f"Real {i+1}",
                value=df_op.at[i, 'Real'],
                key=f"real_op_{i}",
                label_visibility="collapsed"
            )

    st.session_state.tabla_operacional = df_op

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Volver a Empresas"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Revisar Datos Completos →"):
            st.session_state.step = 4
            st.rerun()

# Paso 4: Revisión y guardado
elif st.session_state.step == 4:
    st.header("✅ Paso 4: Revisión Final")
    st.success("Revise todos los datos antes de guardar:")

    with st.expander("📋 Datos Principales", expanded=True):
        datos = st.session_state.datos_principales
        cols = st.columns(2)
        with cols[0]:
            st.metric("Fecha", datos['fecha'])
            st.metric("ABC Seguridad", datos['abc_seguridad'])
        with cols[1]:
            st.metric("Tiempo Salar", minutos_a_tiempo(datos['tiempo_salar']))
            st.metric("Tiempo Pto. Angamos", datos['tiempo_pto'])

    with st.expander("🏭 Empresas Transportistas", expanded=True):
        df_emp = st.session_state.tabla_empresas.copy()
        df_emp.loc[10, 'Prog.'] = df_emp.loc[:8, 'Prog.'].sum()
        df_emp.loc[10, 'Real'] = df_emp.loc[:8, 'Real'].sum()
        st.dataframe(df_emp.style.highlight_max(axis=0, color='#90EE90'), use_container_width=True)

    with st.expander("📊 Datos Operacionales", expanded=True):
        st.dataframe(st.session_state.tabla_operacional, use_container_width=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← Editar Operacional"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("↻ Editar Principales"):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("💾 Guardar Definitivamente"):
            st.balloons()
            st.success("Datos guardados exitosamente!")
            st.write("Datos Principales:", st.session_state.datos_principales)
            st.write("Empresas Transportistas:")
            st.dataframe(st.session_state.tabla_empresas)
            st.write("Datos Operacionales:")
            st.dataframe(st.session_state.tabla_operacional)
            # Aquí puedes agregar código para guardar en base de datos o archivo