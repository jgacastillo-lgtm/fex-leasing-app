import streamlit as st
import numpy_financial as npf
import pandas as pd
from fpdf import FPDF
import base64
import os
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="FEX Capital - Calculadora de Arrendamiento", layout="wide")

LOGO_PATH = "LOGO FEX.png"

# 2. Clase para PDF (Diseño Financiero Desglosado)
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

# 3. Motor Financiero Desglosado
def calcular_escenario(precio_con_iva, tasa_anual, meses, residual_porc, comision_porc):
    precio_base = precio_con_iva / 1.16
    tasa_mensual = (tasa_anual / 100) / 12
    
    # Cálculos Renta
    monto_residual = precio_base * (residual_porc / 100)
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio_base, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    # Cálculos Comisión
    comision_neta = precio_base * (comision_porc / 100)
    comision_iva = comision_neta * 0.16
    comision_total = comision_neta + comision_iva
    
    # Cálculos Pago Inicial
    pago_inicial_neto = renta_neta + comision_neta + renta_neta
    pago_inicial_iva = iva_renta + comision_iva + iva_renta
    pago_inicial_total = renta_total + comision_total + renta_total
    
    # Cálculos Residual
    residual_neto = monto_residual
    residual_iva = residual_neto * 0.16
    residual_total = residual_neto + residual_iva
    
    return {
        "precio_base": precio_base,
        "tasa_mensual": tasa_mensual,
        "renta_neta": renta_neta,
        "iva_renta": iva_renta,
        "renta_total": renta_total,
        "comision_neta": comision_neta,
        "comision_iva": comision_iva,
        "comision_total": comision_total,
        "pago_inicial_neto": pago_inicial_neto,
        "pago_inicial_iva": pago_inicial_iva,
        "pago_inicial_total": pago_inicial_total,
        "residual_neto": residual_neto,
        "residual_iva": residual_iva,
        "residual_total": residual_total
    }

# 4. Interfaz Lateral
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    st.sidebar.markdown("<p style='text-align: center; font-weight: bold; color: #1B1B1B; margin-top: -10px;'>TU ALIADO FINANCIERO</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
st.sidebar.markdown("### Configuración de Parámetros")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio_input = st.sidebar.number_input("Precio del Equipo (IVA incluido)", min_value=1000.0, value=1160000.0, step=10000.0, format="%.2f")
tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo Forzoso (Meses)", 6, 72, 36, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 10, 1)
comision = st.sidebar.number_input("Comisión por Apertura (%)", min_value=0.0, value=3.0, step=0.5, format="%.2f")

# 5. Captura Datos
st.title("Calculadora de Arrendamiento")
st.markdown("---")

with st.expander("Información Legal del Cliente", expanded=True):
    c_c1, c_c2 = st.columns(2)
    nombre_empresa = c_c1.text_input("Razón Social / Empresa", "SEPRINAL")
    rfc_cliente = c_c1.text_input("RFC", "ABC123456XYZ")
    representante = c_c2.text_input("Representante Legal", "Juanito Caminador")
    equipo_desc = c_c2.text_input("Descripción del Activo", "Equipo de Transporte")

# Ejecución de Cálculos
vals = calcular_escenario(precio_input, tasa, meses, residual, comision)

# 6. Resumen de Condiciones (Web)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Resumen de la Operación")

# Creación de Tablas para la Web
df_firma = pd.DataFrame({
    "Concepto": ["1era Renta Anticipada", "Comisión por Apertura", "Renta en Garantía", "TOTAL A LA FIRMA"],
    "Valor Neto": [f"{moneda} ${vals['renta_neta']:,.2f}", f"{moneda} ${vals['comision_neta']:,.2f}", f"{moneda} ${vals['renta_neta']:,.2f}", f"{moneda} ${vals['pago_inicial_neto']:,.2f}"],
    "I.V.A.": [f"{moneda} ${vals['iva_renta']:,.2f}", f"{moneda} ${vals['comision_iva']:,.2f}", f"{moneda} ${vals['iva_renta']:,.2f}", f"{moneda} ${vals['pago_inicial_iva']:,.2f}"],
    "Valor Total": [f"{moneda} ${vals['renta_total']:,.2f}", f"{moneda} ${vals['comision_total']:,.2f}", f"{moneda} ${vals['renta_total']:,.2f}", f"{moneda} ${vals['pago_inicial_total']:,.2f}"]
})

df_mensualidades = pd.DataFrame({
    "Concepto": [f"{meses - 2} pagos con periodicidad Mensual"],
    "Valor Neto": [f"{moneda} ${vals['renta_neta']:,.2f}"],
    "I.V.A.": [f"{moneda} ${vals['iva_renta']:,.2f}"],
    "Valor Total": [f"{moneda} ${vals['renta_total']:,.2f}"]
})

df_termino = pd.DataFrame({
    "Concepto": ["Valor Residual / Opción de Compra"],
    "Valor Neto": [f"{moneda} ${vals['residual_neto']:,.2f}"],
    "I.V.A.": [f"{moneda} ${vals['residual_iva']:,.2f}"],
    "Valor Total": [f"{moneda} ${vals['residual_total']:,.2f}"]
})

st.markdown("**A la firma del contrato se pagará:**")
st.dataframe(df_firma, use_container_width=True, hide_index=True)

st.markdown("**Mensualidades:**")
st.dataframe(df_mensualidades, use_container_width=True, hide_index=True)

st.markdown("**Al término del contrato:**")
st.dataframe(df_termino, use_container_width=True, hide_index=True)

# Vista Interna para FEX (Amortización)
with st.expander("Vista Analítica Interna (Exclusivo FEX Capital)"):
    st.info(f"Monto a Financiar (Base sin IVA): {moneda} ${vals['precio_base']:,.2f}")
    
    datos_internos = []
    saldo_insoluto = vals['precio_base']
    for mes in range(1, meses + 1):
        interes_mes = 0 if mes == 1 else saldo_insoluto * vals['tasa_mensual']
        capital_mes = vals['renta_neta'] - interes_mes
        saldo_insoluto -= capital_mes
        datos_internos.append({
            "Mes": mes,
            "Renta (sin IVA)": vals['renta_neta'],
            "Interés": interes_mes,
            "Amortización Capital": capital_mes,
            "Saldo Insoluto": max(saldo_insoluto, 0)
        })
    st.dataframe(pd.DataFrame(datos_internos).style.format({
        "Renta (sin IVA)": "{:,.2f}", "Interés": "{:,.2f}", "Amortización Capital": "{:,.2f}", "Saldo Insoluto": "{:,.2f}"
    }), use_container_width=True)

# 7. Botón PDF
st.markdown("---")
if st.button("Generar y Descargar Term Sheet PDF"):
    pdf = TermSheetPDF()
    pdf.add_page()
    pdf.set_text_color(27, 27, 27)
    
    # Información General
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. INFORMACION GENERAL", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, f"Cliente: {nombre_empresa}", 0, 0)
    pdf.cell(95, 7, f"RFC: {rfc_cliente}", 0, 1)
    pdf.cell(0, 7, f"Activo: {equipo_desc}", ln=True)
    pdf.cell(0, 7, f"Valor del Activo (IVA inc): {moneda} ${precio_input:,.2f}", ln=True)
    pdf.ln(5)

    # Bloque 1: A la firma del contrato
    pdf.set_fill_color(210, 210, 210) 
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "A la firma del contrato se pagara", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 7, "", 0, 0)
    pdf.cell(38, 7, "Valor Neto", 0, 0, 'R')
    pdf.cell(38, 7, "I.V.A.", 0, 0, 'R')
    pdf.cell(39, 7, "Valor Total", 0, 1, 'R')
    
    pdf.set_font("Arial", '', 9)
    pdf.cell(75, 6, "1era Renta Anticipada:", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['renta_neta']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['iva_renta']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['renta_total']:,.2f}", 0, 1, 'R')
    pdf.cell(75, 6, "Comision por Apertura:", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['comision_neta']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['comision_iva']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['comision_total']:,.2f}", 0, 1, 'R')
    pdf.cell(75, 6, "Renta en Garantia:", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['renta_neta']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['iva_renta']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['renta_total']:,.2f}", 0, 1, 'R')
    
    pdf.cell(190, 2, "", "B", 1) # Linea separadora
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 6, "TOTALES :", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['pago_inicial_neto']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['pago_inicial_iva']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['pago_inicial_total']:,.2f}", 0, 1, 'R')
    pdf.ln(5)

    # Bloque 2: Mensualidades
    pdf.set_fill_color(210, 210, 210)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "Mensualidades", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 7, "", 0, 0)
    pdf.cell(38, 7, "Mensualidad", 0, 0, 'R')
    pdf.cell(38, 7, "I.V.A.", 0, 0, 'R')
    pdf.cell(39, 7, "Total Mensual", 0, 1, 'R')
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 6, f"{meses - 2} pagos con periodicidad Mensual.", 0, 0, 'C'); pdf.cell(38, 6, f"{vals['renta_neta']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['iva_renta']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['renta_total']:,.2f}", 0, 1, 'R')
    pdf.ln(8)

    # Bloque 3: Al termino del contrato
    pdf.set_fill_color(210, 210, 210)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "Al termino del contrato", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 7, "Valor Residual / Opcion de Compra:", 0, 0, 'R'); pdf.cell(38, 7, f"{vals['residual_neto']:,.2f}", 0, 0, 'R'); pdf.cell(38, 7, f"{vals['residual_iva']:,.2f}", 0, 0, 'R'); pdf.cell(39, 7, f"{vals['residual_total']:,.2f}", 0, 1, 'R')
    
    # Firmas
    pdf.ln(25)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 10, "__________________________________", 0, 0, 'C'); pdf.cell(90, 10, "__________________________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C'); pdf.cell(90, 5, "Por: FEX CAPITAL, S.A. DE C.V.", 0, 1, 'C')
    pdf.cell(90, 5, f"{representante}", 0, 0, 'C'); pdf.cell(90, 5, "Representante Legal", 0, 1, 'C')
    
    # Generar descarga
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    st.markdown(f'<br><a href="data:application/pdf;base64,{b64_pdf}" download="Propuesta_FEX_{nombre_empresa}.pdf" style="padding:12px 20px; background-color:#0163FF; color:white; font-weight:bold; border-radius:4px; text-decoration:none; display:inline-block;">Descargar Propuesta PDF</a>', unsafe_allow_html=True)
