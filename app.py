import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from PIL import Image
from fpdf import FPDF
import tempfile
import os
from pathlib import Path
import numpy as np

# Configuración global
pio.templates.default = "plotly"
COLOR_PALETTE = px.colors.qualitative.Plotly

# Función robusta para normalizar nombres de empresa
def normalizar_nombre_empresa(nombre):
    nombre = str(nombre).strip().upper()
    nombre = nombre.replace('.', '').replace('&', 'AND')
    nombre = ' '.join(nombre.split())  # Normaliza espacios múltiples
    equivalencias = {
        # JORQUERA TRANSPORTE S. A.
        "JORQUERA TRANSPORTE S A": "JORQUERA TRANSPORTE S. A.",
        # M S & D SPA y variantes
        "MINING SERVICES AND DERIVATES": "M S & D SPA",
        "MINING SERVICES AND DERIVATES SPA": "M S & D SPA",
        "M S AND D": "M S & D SPA",
        "M S AND D SPA": "M S & D SPA",
        "MSANDD SPA": "M S & D SPA",
        "M S D": "M S & D SPA",
        "M S D SPA": "M S & D SPA",
        "M S & D": "M S & D SPA",
        "M S & D SPA": "M S & D SPA",
        "MS&D SPA": "M S & D SPA",
        # M&Q SPA y variantes
        "M AND Q SPA": "M&Q SPA",
        "M AND Q": "M&Q SPA",
        "M Q SPA": "M&Q SPA",
        "MQ SPA": "M&Q SPA",
        "M&Q SPA": "M&Q SPA",
        "MANDQ SPA": "M&Q SPA",
        "MINING AND QUARRYING SPA": "M&Q SPA",
        "MINING AND QUARRYNG SPA": "M&Q SPA",
        # AG SERVICES SPA
        "AG SERVICE SPA": "AG SERVICES SPA",
        "AG SERVICES SPA": "AG SERVICES SPA",
        # COSEDUCAM S A
        "COSEDUCAM S A": "COSEDUCAM S A"
    }
    return equivalencias.get(nombre, nombre)

# Configuración de la página
st.set_page_config(page_title="Dashboard Equipos por Hora", layout="wide")
CURRENT_DIR = Path(__file__).parent
LOGOS = {
    "COSEDUCAM S A": str(CURRENT_DIR / "coseducam.png"),
    "M&Q SPA": str(CURRENT_DIR / "mq.png"),
    "M S & D SPA": str(CURRENT_DIR / "msd.png"),
    "JORQUERA TRANSPORTE S. A.": str(CURRENT_DIR / "jorquera.png"),
    "AG SERVICES SPA": str(CURRENT_DIR / "ag.png")
}
BANNER_PATH = str(CURRENT_DIR / "image.png")

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

# Opciones para selector de destino (fila 2)
destinos_opciones = [
    "Antofagasta, P De Litio",
    "Calama",
    "Cancha Salitre Cs",
    "Centinela",
    "Centro Logístico Baquedano",
    "Mejillones",
    "MINERAS",
    "Nueva Victoria",
    "Observatorio ALMA",
    "Otros Destinos",
    "Planta TAS, ME",
    "Pta. Muriato",
    "Pta. Npt 2",
    "Pta. Npt-3 Cs",
    "Pta. Npt-4 Cs",
    "Pta. Prilado Cs",
    "Pta. Pts",
    "Puerto Angamos",
    "Puerto Patache",
    "Santiago",
    "Taltal",
    "Tocopilla",
    "Centro URIBE",
    "Bodega Hansa",
    "Bodega Ulog",
    "Bodega Mercosur",
    "pintado",
    "Centro PANG"
]

# Función para convertir tiempo en minutos
def tiempo_a_minutos(tiempo_str):
    try:
        horas, minutos = map(int, tiempo_str.split(':'))
        return horas * 60 + minutos
    except:
        return None

def minutos_a_tiempo(minutos):
    return f"{minutos//60:02d}:{minutos%60:02d}"

# Interfaz principal
st.title("📊 Dashboard: Equipos por Hora, Empresa, Fecha y Destino")

# Paso 1: Datos principales
if st.session_state.step == 1:
    st.header("📝 Paso 1: Datos Principales")

    with st.form("form_principal"):
        fecha = st.date_input("📅 Fecha", value=pd.to_datetime("today").date())
        abc_seguridad = st.selectbox("🔤 ABC de Seguridad", ["A", "B", "C"])
        tiempo_salar = st.text_input("⏳ Tiempo Salar de Atacama (ej: 4:30)", "00:00")
        tiempo_pto = st.text_input("⏱️ Tiempo Pto. Angamos (ej: 5:15)", "00:00")

        if st.form_submit_button("→ Siguiente"):
            tiempo_salar_min = tiempo_a_minutos(tiempo_salar)
            tiempo_pto_min = tiempo_a_minutos(tiempo_pto)

            if None in [tiempo_salar_min, tiempo_pto_min]:
                st.error("⚠️ Formato de tiempo incorrecto. Use HH:MM")
            else:
                st.session_state.datos_principales = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'abc_seguridad': abc_seguridad,
                    'tiempo_salar': tiempo_salar,
                    'tiempo_pto': tiempo_pto
                }
                st.session_state.step = 2
                st.rerun()

# Paso 2: Tabla de empresas transportistas
elif st.session_state.step == 2:
    st.header("🏭 Paso 2: Empresas Transportistas")
    df = st.session_state.tabla_empresas.copy()

    for i in range(len(df)-1):
        if df.loc[i, 'Empresas Transportistas']:
            cols = st.columns([4, 2, 2])
            with cols[0]:
                st.markdown(f"**{df.loc[i, 'Empresas Transportistas']}**")
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
        if st.button("→ Siguiente"):
            st.session_state.tabla_empresas = df
            st.session_state.step = 3
            st.rerun()

# Paso 3: Tabla operacional con filas fijas
elif st.session_state.step == 3:
    st.header("📊 Paso 3: Datos Operacionales por Sector")
    df_op = st.session_state.tabla_operacional.copy()
    nombres_filas = df_op['Concepto'].tolist()

    st.write("Complete los valores programados y reales para cada indicador:")

    for i in range(12):
        cols = st.columns([3, 2, 2])
        with cols[0]:
            st.markdown(f"**{nombres_filas[i]}**")

        # Fila 0: Selector de sector
        if i == 0:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.selectbox(
                    "Sector",
                    sectores_opciones,
                    index=sectores_opciones.index(df_op.at[i, 'Programado']) if df_op.at[i, 'Programado'] in sectores_opciones else 0,
                    key=f"sector_{i}",
                    label_visibility="collapsed"
                )

        # Fila 1: Selector de producto
        elif i == 1:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.selectbox(
                    "Producto",
                    productos_opciones,
                    index=productos_opciones.index(df_op.at[i, 'Programado']) if df_op.at[i, 'Programado'] in productos_opciones else 0,
                    key=f"producto_{i}",
                    label_visibility="collapsed"
                )

        # Fila 2: Selector de destino
        elif i == 2:
            with cols[1]:
                df_op.at[i, 'Programado'] = st.selectbox(
                    "Destino",
                    destinos_opciones,
                    index=destinos_opciones.index(df_op.at[i, 'Programado']) if df_op.at[i, 'Programado'] in destinos_opciones else 0,
                    key=f"destino_{i}",
                    label_visibility="collapsed"
                )

        # Resto de las filas: campos normales
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
        if st.button("🔍 Revisar Datos Completos →"):
            st.session_state.step = 4
            st.rerun()

# Paso 4: Revisión final
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
            st.metric("Tiempo Salar", datos['tiempo_salar'])
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

    if st.checkbox("Descargar datos como CSV"):
        combined_df = pd.concat([
            pd.DataFrame([st.session_state.datos_principales]),
            st.session_state.tabla_empresas.add_prefix('Empresa_'),
            st.session_state.tabla_operacional.add_prefix('Operacional_')
        ], axis=1)
        csv_data = combined_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Descargar CSV", data=csv_data, file_name="registro_completo.csv", mime="text/csv")

# Paso 5: Carga Excel y visualización avanzada
st.markdown("---")
st.subheader("📂 Cargar Archivo Excel (.xlsx o .xlsm)")
uploaded_file = st.file_uploader("Carga tu archivo Excel", type=["xlsx", "xlsm"])

if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        df_excel = pd.read_excel(tmp_path, engine='openpyxl')

        required_columns = {
            'fecha_col': 0,     # Columna A
            'destino_col': 3,   # Columna D
            'empresa_col': 11,  # Columna L
            'hora_col': 14      # Columna O
        }

        if len(df_excel.columns) < max(required_columns.values()) + 1:
            st.error("El archivo no tiene el formato esperado.")
            st.stop()

        fecha_col = df_excel.columns[required_columns['fecha_col']]
        destino_col = df_excel.columns[required_columns['destino_col']]
        empresa_col = df_excel.columns[required_columns['empresa_col']]
        hora_col = df_excel.columns[required_columns['hora_col']]

        df_excel = df_excel.dropna(subset=[fecha_col, destino_col, empresa_col, hora_col])

        df_excel[fecha_col] = pd.to_datetime(df_excel[fecha_col], errors='coerce', dayfirst=True)
        df_excel[hora_col] = pd.to_datetime(df_excel[hora_col], format='%H:%M:%S', errors='coerce').dt.hour

        df_excel[empresa_col] = df_excel[empresa_col].apply(normalizar_nombre_empresa)

        fechas_disponibles = df_excel[fecha_col].dropna().dt.date.unique()
        if len(fechas_disponibles) == 0:
            st.warning("No se encontraron fechas válidas en el archivo.")
        else:
            fecha_sel = st.date_input(
                "Selecciona la fecha:",
                min_value=min(fechas_disponibles),
                max_value=max(fechas_disponibles),
                value=min(fechas_disponibles)
            )
            df_filtrado = df_excel[df_excel[fecha_col].dt.date == fecha_sel]
            destinos = sorted(df_filtrado[destino_col].dropna().unique())
            destinos_sel = st.multiselect("Selecciona destino(s):", destinos, default=list(destinos))
            empresas = sorted(df_filtrado[empresa_col].dropna().unique())
            empresas_sel = st.multiselect("Selecciona empresa(s):", empresas, default=list(empresas))

            df_filtrado = df_filtrado[
                df_filtrado[destino_col].isin(destinos_sel) &
                df_filtrado[empresa_col].isin(empresas_sel)
            ]

            horas = df_filtrado[hora_col].dropna().unique()
            if len(horas) > 0:
                min_hora, max_hora = int(min(horas)), int(max(horas))
                hora_rango = st.slider("Selecciona rango de horas:", min_hora, max_hora, (min_hora, max_hora), step=1)
                df_filtrado = df_filtrado[(df_filtrado[hora_col] >= hora_rango[0]) & (df_filtrado[hora_col] <= hora_rango[1])]

            horas_labels = [f"{str(h).zfill(2)}:00 - {str(h).zfill(2)}:59" for h in range(24)]
            df_filtrado['Hora Intervalo'] = df_filtrado[hora_col].apply(
                lambda h: f"{str(int(h)).zfill(2)}:00 - {str(int(h)).zfill(2)}:59"
            )

            for empresa in empresas_sel:
                empresa_normalizada = normalizar_nombre_empresa(empresa)
                st.markdown(f"---\n### Empresa: {empresa}")

                col1, col2 = st.columns([2, 2])
                with col1:
                    try:
                        if os.path.exists(BANNER_PATH):
                            st.image(BANNER_PATH, use_container_width=True)
                        logo_path = LOGOS.get(empresa_normalizada)
                        if logo_path and os.path.exists(logo_path):
                            st.image(logo_path, width=120)
                        else:
                            st.info(f"No se encontró logo para {empresa}")
                    except Exception as e:
                        st.warning(f"Error al cargar imágenes: {str(e)}")

                    df_empresa = df_filtrado[df_filtrado[empresa_col] == empresa_normalizada]
                    resumen = df_empresa.groupby([hora_col, destino_col]).size().reset_index(name='Cantidad')

                    if not resumen.empty:
                        destinos_unicos = resumen[destino_col].unique()
                        color_map = {dest: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, dest in enumerate(destinos_unicos)}
                        fig = px.line(
                            resumen,
                            x=hora_col,
                            y="Cantidad",
                            color=destino_col,
                            markers=True,
                            labels={
                                hora_col: "Hora de Entrada",
                                "Cantidad": "Cantidad de Equipos",
                                destino_col: "Destino"
                            },
                            color_discrete_map=color_map
                        )
                        fig.update_layout(xaxis=dict(dtick=1), title=f"Cantidad de equipos por hora - {empresa}")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay datos para los filtros seleccionados.")

                with col2:
                    tabla = pd.pivot_table(
                        df_empresa,
                        index='Hora Intervalo',
                        columns=destino_col,
                        values=empresa_col,
                        aggfunc='count',
                        fill_value=0
                    )
                    tabla = tabla.reindex(horas_labels, fill_value=0)
                    sumatoria = pd.DataFrame(tabla.sum(axis=0)).T
                    sumatoria.index = ['TOTAL']
                    tabla_final = pd.concat([tabla, sumatoria])
                    st.dataframe(tabla_final.style.format(na_rep="0", precision=0))

                st.markdown("---")
                st.subheader(f"📄 Generar PDF para {empresa}")

                if st.button(f"Generar PDF para {empresa}"):
                    try:
                        with tempfile.TemporaryDirectory() as tmpdir:
                            grafico_path = os.path.join(tmpdir, f"grafico_{empresa}.png")
                            fig.write_image(grafico_path, width=900, height=400, scale=2)

                            images_to_stack = []
                            opened_imgs = []

                            if os.path.exists(BANNER_PATH):
                                banner_img = Image.open(BANNER_PATH)
                                images_to_stack.append(banner_img)
                                opened_imgs.append(banner_img)

                            logo_path = LOGOS.get(empresa_normalizada)
                            if logo_path and os.path.exists(logo_path):
                                logo_img = Image.open(logo_path)
                                logo_width = 120
                                wpercent = (logo_width / float(logo_img.size[0]))
                                hsize = int((float(logo_img.size[1]) * float(wpercent)))
                                logo_img = logo_img.resize((logo_width, hsize), Image.LANCZOS)
                                grafico_img = Image.open(grafico_path)
                                logo_bg = Image.new('RGBA', (grafico_img.width, logo_img.height), (255, 255, 255, 0))
                                logo_bg.paste(logo_img, ((grafico_img.width - logo_width)//2, 0), logo_img if logo_img.mode == 'RGBA' else None)
                                images_to_stack.append(logo_bg.convert('RGB'))

                            grafico_img = Image.open(grafico_path)
                            images_to_stack.append(grafico_img)
                            base_width = images_to_stack[-1].width
                            resized_imgs = []
                            for img in images_to_stack:
                                if img.width != base_width:
                                    wpercent = (base_width / float(img.size[0]))
                                    hsize = int((float(img.size[1]) * float(wpercent)))
                                    img = img.resize((base_width, hsize), Image.LANCZOS)
                                resized_imgs.append(img)

                            total_height = sum(img.height for img in resized_imgs)
                            combined_img = Image.new('RGB', (base_width, total_height), (255, 255, 255))
                            y_offset = 0
                            for img in resized_imgs:
                                combined_img.paste(img, (0, y_offset))
                                y_offset += img.height

                            combined_path = os.path.join(tmpdir, f"combinado_{empresa}.png")
                            combined_img.save(combined_path)

                            pdf = FPDF(orientation='L', unit='mm', format='A4')
                            pdf.add_page()
                            pdf.set_font("Arial", "B", 16)
                            pdf.cell(0, 10, f"Empresa: {empresa}", ln=1, align="C")
                            pdf.ln(5)
                            pdf.image(combined_path, x=10, y=20, w=270)
                            pdf.add_page(orientation='P')
                            pdf.set_font("Arial", "B", 12)
                            pdf.cell(0, 10, "Tabla de equipos por hora y destino", ln=1, align="C")
                            pdf.set_font("Arial", "", 8)

                            col_width = max(20, int(180 / (len(tabla_final.columns)+1)))
                            tabla_reset = tabla_final.reset_index()
                            hora_col_name = tabla_reset.columns[0]

                            pdf.cell(col_width, 8, "Hora", border=1, align="C")
                            for col in tabla_final.columns:
                                pdf.cell(col_width, 8, str(col), border=1, align="C")
                            pdf.ln()
                            for idx, row in tabla_reset.iterrows():
                                hora_label = row[hora_col_name]
                                if pd.isnull(hora_label):
                                    hora_label = "TOTAL"
                                pdf.cell(col_width, 8, str(hora_label), border=1, align="C")
                                for col in tabla_final.columns:
                                    pdf.cell(col_width, 8, str(int(row[col])), border=1, align="C")
                                pdf.ln()

                            pdf_path = os.path.join(tmpdir, f"dashboard_{empresa}.pdf")
                            pdf.output(pdf_path)
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button(
                                label=f"⬇️ Descargar PDF para {empresa}",
                                data=pdf_bytes,
                                file_name=f"dashboard_{empresa}.pdf",
                                mime="application/pdf"
                            )

                    except Exception as e:
                        st.error(f"Error al generar PDF: {str(e)}")

    except Exception as e:
        st.error(f"Error al procesar archivo: {str(e)}")

# Botón para reiniciar formulario
if st.session_state.step == 4:
    if st.button("🔄 Reiniciar formulario"):
        st.session_state.clear()
        st.rerun()