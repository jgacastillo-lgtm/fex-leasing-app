import streamlit as st
import numpy_financial as npf
import pandas as pd
from fpdf import FPDF
import base64
import os
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="FEX Capital - Sistema de Arrendamiento", layout="wide")

LOGO_PATH = "LOGO FEX.png"

# 2. Clase para PDF (Diseño Ejecutivo sin Tabla)
class TermSheetPDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=80, y=10, w=50)
        self.set_y(38)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(27, 27, 27) 
        self.cell(0, 6, 'TERM SHEET PRELIMINAR', 0, 1, 'C')
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        self.set_font('Arial', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Fecha: {fecha_hoy}', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# 3. Motor Financiero con Renta en Garantía
def calcular_escenario(precio_con_iva, tasa_anual, meses, residual_porc, comision_porc):
    precio_base = precio_con_iva / 1.16
    tasa_mensual = (tasa_anual / 100) / 12
    monto_residual = precio_base * (residual_porc / 100)
    
    # Renta Neta (Anticipada)
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio_base, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    # Comisión
    monto_comision = precio_base * (comision_porc / 100)
    
    # NUEVO DESEMBOLSO INICIAL: 1ra Renta + Comisión + Renta en Garantía
    # Ambas rentas (1ra y garantía) incluyen IVA
    pago_inicial = (renta_total * 2) + monto_comision
    
    return precio_base, renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual

# 4. Interfaz Lateral
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    st.sidebar.markdown("<p style='text-align: center; font-weight: bold; color: #1B1B1B; margin-top: -10px;'>TU ALIADO FINANCIERO</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
st.sidebar.markdown("### Configuración de Parámetros")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio_input = st.sidebar.number_input("Precio del Equipo (IVA incluido)", min_value=1000.0, value=1160000.0, step=10000.0, format="%.2f")
tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo Forzoso (Meses)", 6, 72, 24, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 1, 1)
comision = st.sidebar.number_input("Comisión por Apertura (%)", min_value=0.0, value=2.0, step=0.5, format="%.2f")

# 5. Captura Datos
st.title("Calculadora de Arrendamiento")
st.markdown("---")

with st.expander("Información Legal del Cliente", expanded=True):
    c_c1, c_c2 = st.columns(2)
    nombre_empresa = c_c1.text_input("Razón Social / Empresa", "SEPRINAL")
    rfc_cliente = c_c1.text_input("RFC", "ABC123456XYZ")
    representante = c_c2.text_input("Representante Legal", "Juanito Caminador")
    equipo_desc = c_c2.text_input("Descripción del Activo", "Equipo de Transporte")

# Cálculos
p_base, r_neta, i_renta, r_total, m_comision, p_inicial, m_residual = calcular_escenario(
    precio_input, tasa, meses, residual, comision
)

# 6. Resumen Ejecutivo Web
st.markdown("### Resumen de la Operación")
res1, res2, res3 = st.columns(3)
res1.metric("Pago Inicial Total", f"{moneda} ${p_inicial:,.2f}")
res2.metric("Renta Mensual Total", f"{moneda} ${r_total:,.2f}")
res3.metric("Valor Residual Final", f"{moneda} ${m_residual:,.2f}")

# 7. Botón PDF y Generación
st.markdown("---")
if st.button("Generar y Descargar Term Sheet PDF"):
    pdf = TermSheetPDF()
    pdf.add_page()
    pdf.set_text_color(27, 27, 27)
    
    # SECCIÓN 1: CLIENTE Y EQUIPO
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "1. INFORMACIÓN GENERAL", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, f"Cliente: {nombre_empresa}", 0, 0)
    pdf.cell(95, 7, f"RFC: {rfc_cliente}", 0, 1)
    pdf.cell(0, 7, f"Activo: {equipo_desc}", ln=True)
    pdf.cell(0, 7, f"Valor del Activo (IVA inc): {moneda} ${precio_input:,.2f}", ln=True)
    pdf.ln(5)

    # SECCIÓN 2: DESEMBOLSO AL FIRMAR (LO QUE PAGA HOY)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "2. DESEMBOLSO INICIAL (AL FIRMAR)", ln=True, border='B', fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(130, 7, "Primera Renta Anticipada (con IVA):", 0, 0); pdf.cell(0, 7, f"{moneda} ${r_total:,.2f}", 0, 1, 'R')
    pdf.cell(130, 7, f"Comisión por Apertura ({comision}%):", 0, 0); pdf.cell(0, 7, f"{moneda} ${m_comision:,.2f}", 0, 1, 'R')
    pdf.cell(130, 7, "Renta en Garantía (Última mensualidad con IVA):", 0, 0); pdf.cell(0, 7, f"{moneda} ${r_total:,.2f}", 0, 1, 'R')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(130, 8, "TOTAL A PAGAR AL FIRMAR:", 'T', 0); pdf.cell(0, 8, f"{moneda} ${p_inicial:,.2f}", 'T', 1, 'R')
    pdf.ln(5)

    # SECCIÓN 3: DURANTE EL CONTRATO
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "3. ESTRUCTURA DE PAGOS MENSUALES", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(130, 7, "Renta Base (sin IVA):", 0, 0); pdf.cell(0, 7, f"{moneda} ${r_neta:,.2f}", 0, 1, 'R')
    pdf.cell(130, 7, "IVA (16%):", 0, 0); pdf.cell(0, 7, f"{moneda} ${i_renta:,.2f}", 0, 1, 'R')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(130, 8, "PAGO MENSUAL TOTAL:", 'T', 0); pdf.cell(0, 8, f"{moneda} ${r_total:,.2f}", 'T', 1, 'R')
    pdf.set_font("Arial", 'I', 9)
    # Se restan 2 porque la 1ra y la última ya se pagaron
    pdf.cell(0, 7, f"* El cliente realizará {meses - 2} pagos mensuales adicionales durante el plazo forzoso.", ln=True)
    pdf.ln(5)

    # SECCIÓN 4: TÉRMINO DEL CONTRATO
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "4. AL FINALIZAR EL CONTRATO", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(130, 7, f"Opción de Compra / Valor Residual ({residual}%):", 0, 0); pdf.cell(0, 7, f"{moneda} ${m_residual:,.2f}", 0, 1, 'R')
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 7, "* La renta en garantía pagada al inicio se aplicará para cubrir la última mensualidad del plazo.", ln=True)

    # FIRMAS
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 10, "__________________________________", 0, 0, 'C'); pdf.cell(90, 10, "__________________________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C'); pdf.cell(90, 5, "Por: FEX CAPITAL, S.A. DE C.V.", 0, 1, 'C')
    pdf.cell(90, 5, f"{representante}", 0, 0, 'C'); pdf.cell(90, 5, "Representante Legal", 0, 1, 'C')
    
    # Generar descarga
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    st.markdown(f'<br><a href="data:application/pdf;base64,{b64_pdf}" download="Propuesta_FEX_{nombre_empresa}.pdf" style="padding:12px 20px; background-color:#0163FF; color:white; font-weight:bold; border-radius:4px; text-decoration:none; display:inline-block;">📥 Descargar Propuesta PDF</a>', unsafe_allow_html=True)

st.info("Nota: Esta propuesta no incluye la tabla de amortización detallada en el PDF por políticas de simplificación comercial.")
