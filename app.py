import streamlit as st
import numpy_financial as npf
import pandas as pd
from fpdf import FPDF
import base64

# 1. Configuración de la página
st.set_page_config(page_title="FEX Capital - Term Sheet Generator", page_icon="🏢", layout="wide")

# 2. Clase para el PDF (Basada en nuestra validación en Colab)
class TermSheetPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'TERM SHEET PRELIMINAR', 0, 1, 'C')
        self.set_font('Arial', 'B', 11)
        self.set_text_color(41, 128, 185)
        self.cell(0, 10, 'FEX CAPITAL LOANS, S.A. DE C.V., SOFOM, E.N.R.', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# 3. Motor Financiero
def calcular_escenario(precio, tasa_anual, meses, residual_porc, comision_porc):
    tasa_mensual = (tasa_anual / 100) / 12
    monto_residual = precio * (residual_porc / 100)
    # Renta Anticipada (when=1)
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    monto_comision = precio * (comision_porc / 100)
    pago_inicial = renta_total + monto_comision
    return renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual

# 4. Interfaz de Usuario (Panel Lateral)
st.sidebar.header("⚙️ Configuración del Crédito")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio = st.sidebar.number_input("Precio del Equipo (sin IVA)", min_value=1000, value=1000000)
tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo (Meses)", 6, 72, 24, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 0, 1)
comision = st.sidebar.number_input("Comisión Apertura (%)", min_value=0.0, value=2.0, step=0.5)

# 5. Captura de Datos del Cliente (Panel Principal)
st.title("🏢 Generador de Term Sheet - FEX Capital")
st.markdown("Complete los datos para formalizar la propuesta técnica.")

with st.expander("📝 Datos Legales del Cliente", expanded=True):
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        nombre_empresa = st.text_input("Nombre de la Empresa / Cliente", "SEPRINAL")
        rfc_cliente = st.text_input("RFC", "ABC123456XYZ")
    with col_c2:
        representante = st.text_input("Representante Legal", "Juanito Caminador")
        equipo_desc = st.text_input("Descripción del Equipo", "Equipo de Transporte")

# Cálculos instantáneos
r_neta, i_renta, r_total, m_comision, p_inicial, m_residual = calcular_escenario(
    precio, tasa, meses, residual, comision
)

# 6. Resumen Ejecutivo Visual
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Renta Total Mensual", f"{moneda} ${r_total:,.2f}")
c2.metric("Desembolso Inicial", f"{moneda} ${p_inicial:,.2f}")
c3.metric("Valor Residual", f"{moneda} ${m_residual:,.2f}")

# 7. Tabla de Pagos
datos_tabla = []
for mes in range(1, meses + 1):
    p_mes = r_total + m_comision if mes == 1 else r_total
    datos_tabla.append({
        "Mes": mes,
        "Renta Base": f"{moneda} ${r_neta:,.2f}",
        "IVA": f"{moneda} ${i_renta:,.2f}",
        "Pago Total": f"{moneda} ${p_mes:,.2f}",
        "Concepto": "1ra Renta + Comisión" if mes == 1 else "Renta Mensual"
    })
df_pagos = pd.DataFrame(datos_tabla)

# 8. Botón para Generar PDF
if st.button("🚀 Generar y Descargar Term Sheet"):
    pdf = TermSheetPDF()
    pdf.add_page()
    
    # Sección 1: Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. DATOS DEL CLIENTE", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"Empresa: {nombre_empresa}", ln=True)
    pdf.cell(0, 8, f"RFC: {rfc_cliente}", ln=True)
    pdf.cell(0, 8, f"Representante Legal: {representante}", ln=True)
    
    # Sección 2: Condiciones
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. CONDICIONES Y ESTRUCTURA", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"Activo: {equipo_desc}", ln=True)
    pdf.cell(0, 8, f"Precio de Venta: {moneda} ${precio:,.2f}", ln=True)
    pdf.cell(0, 8, f"Plazo: {meses} meses", ln=True)
    pdf.cell(0, 8, f"Renta Mensual Total: {moneda} ${r_total:,.2f}", ln=True)
    pdf.cell(0, 8, f"Valor Residual: {moneda} ${m_residual:,.2f}", ln=True)
    
    # Pago Inicial Destacado
    pdf.ln(5)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"TOTAL A PAGAR AL FIRMAR: {moneda} ${p_inicial:,.2f}", ln=True, fill=True, align='C')
    
    # Firmas
    pdf.ln(20)
    pdf.cell(90, 10, "__________________________", 0, 0, 'C')
    pdf.cell(90, 10, "__________________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C')
    pdf.cell(90, 5, "Por: FEX CAPITAL LOANS", 0, 1, 'C')

    # Página 2: Tabla
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "ANEXO A: TABLA DE PAGOS PROYECTADA", ln=True, border='B')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(15, 7, "Mes", 1)
    pdf.cell(40, 7, "Renta Base", 1)
    pdf.cell(35, 7, "IVA", 1)
    pdf.cell(40, 7, "Pago Total", 1)
    pdf.cell(55, 7, "Concepto", 1, 1)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_pagos.iterrows():
        pdf.cell(15, 6, str(row['Mes']), 1)
        pdf.cell(40, 6, row['Renta Base'], 1)
        pdf.cell(35, 6, row['IVA'], 1)
        pdf.cell(40, 6, row['Pago Total'], 1)
        pdf.cell(55, 6, row['Concepto'], 1, 1)

    # Generar descarga
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="Term_Sheet_FEX_{nombre_empresa}.pdf" style="text-decoration:none; padding:10px 20px; background-color:#2980b9; color:white; border-radius:5px;">📥 Haz clic aquí para descargar tu PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

st.markdown("---")
st.subheader("📊 Visualización de la Tabla")
st.dataframe(df_pagos, use_container_width=True, hide_index=True)
