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

# 2. Clase para PDF 
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

# 3. Motor Financiero
def calcular_escenario(precio_con_iva, tasa_anual, meses, residual_porc, comision_porc):
    precio_base = precio_con_iva / 1.16
    tasa_mensual = (tasa_anual / 100) / 12
    monto_residual = precio_base * (residual_porc / 100)
    
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio_base, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    monto_comision = precio_base * (comision_porc / 100)
    pago_inicial = renta_total + monto_comision
    
    return precio_base, renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual, tasa_mensual

# 4. Interfaz Lateral
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    st.sidebar.markdown("---")
    
st.sidebar.markdown("### Configuración de Parámetros")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])

# Actualización a formato de moneda con decimales (.00)
precio_input = st.sidebar.number_input("Precio del Equipo (IVA incluido)", min_value=1000.0, value=1160000.0, step=10000.0, format="%.2f")

tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo Forzoso (Meses)", 6, 72, 36, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 10, 1)
comision = st.sidebar.number_input("Comisión por Apertura (%)", min_value=0.0, value=3.0, step=0.5, format="%.2f")

# 5. Captura Datos
st.title("FEX CAPITAL")
st.markdown("#### TU ALIADO FINANCIERO")
st.markdown("---")

with st.expander("Información Legal del Cliente", expanded=True):
    c_c1, c_c2 = st.columns(2)
    nombre_empresa = c_c1.text_input("Razón Social / Empresa", "SEPRINAL")
    rfc_cliente = c_c1.text_input("RFC", "ABC123456XYZ")
    representante = c_c2.text_input("Representante Legal", "Juanito Caminador")
    equipo_desc = c_c2.text_input("Descripción del Activo", "Equipo de Transporte")

# Cálculos
p_base, r_neta, i_renta, r_total, m_comision, p_inicial, m_residual, t_mensual = calcular_escenario(
    precio_input, tasa, meses, residual, comision
)

# 6. Resumen Ejecutivo
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Resumen de la Propuesta")
res1, res2, res3 = st.columns(3)
res1.metric("Renta Mensual Total", f"{moneda} ${r_total:,.2f}")
res2.metric("Desembolso Inicial Requerido", f"{moneda} ${p_inicial:,.2f}")
res3.metric("Valor Residual Fijo", f"{moneda} ${m_residual:,.2f}")

# 7. TABLAS
datos_comerciales = []
datos_internos = []
saldo_insoluto = p_base

for mes in range(1, meses + 1):
    interes_mes = 0 if mes == 1 else saldo_insoluto * t_mensual
    capital_mes = r_neta - interes_mes
    saldo_insoluto -= capital_mes
    
    p_mes = r_total + m_comision if mes == 1 else r_total
    datos_comerciales.append({
        "Mes": mes,
        "Renta Base": f"{moneda} ${r_neta:,.2f}",
        "IVA": f"{moneda} ${i_renta:,.2f}",
        "Pago Total": f"{moneda} ${p_mes:,.2f}",
        "Concepto": "1ra Renta Anticipada + Comisión" if mes == 1 else "Renta Mensual"
    })
    
    datos_internos.append({
        "Mes": mes,
        "Renta (sin IVA)": r_neta,
        "Interés": interes_mes,
        "Amortización Capital": capital_mes,
        "Saldo Insoluto": max(saldo_insoluto, 0)
    })

df_comercial = pd.DataFrame(datos_comerciales)
df_interno = pd.DataFrame(datos_internos)

# Vista Web
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Proyección de Flujos (Cliente)")
st.dataframe(df_comercial, use_container_width=True, hide_index=True)

with st.expander("Vista Analítica Interna (Exclusivo FEX Capital)"):
    st.info(f"Monto a Financiar (Base sin IVA): {moneda} ${p_base:,.2f}")
    st.dataframe(df_interno.style.format({
        "Renta (sin IVA)": "{:,.2f}", "Interés": "{:,.2f}", "Amortización Capital": "{:,.2f}", "Saldo Insoluto": "{:,.2f}"
    }), use_container_width=True)

# 8. Botón PDF
st.markdown("---")
if st.button("Generar y Descargar Term Sheet PDF"):
    pdf = TermSheetPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_text_color(27, 27, 27)
    
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "1. DATOS DEL CLIENTE", ln=True, border='B')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Razón Social: {nombre_empresa}", ln=True); pdf.cell(0, 8, f"RFC: {rfc_cliente}", ln=True)
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "2. CONDICIONES FINANCIERAS", ln=True, border='B')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Activo a Arrendar: {equipo_desc}", ln=True); pdf.cell(0, 8, f"Plazo Forzoso: {meses} meses", ln=True)
    pdf.cell(0, 8, f"Valor Total del Equipo (IVA incluido): {moneda} ${precio_input:,.2f}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 245, 255) 
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"DESEMBOLSO INICIAL REQUERIDO: {moneda} ${p_inicial:,.2f}", ln=True, fill=True, align='C')
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "(Incluye primera renta anticipada, IVA y comision por apertura)", ln=True, align='C')
    
    pdf.ln(15); pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 10, "__________________________________", 0, 0, 'C'); pdf.cell(90, 10, "__________________________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C')
    pdf.cell(90, 5, "Por: FEX CAPITAL, S.A. DE C.V.", 0, 1, 'C')
    
    # Anexo A
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "ANEXO A: PROYECCION DE FLUJOS", ln=True, border='B'); pdf.ln(5)
    
    def imprimir_encabezados_tabla(pdf_obj):
        pdf_obj.set_fill_color(1, 99, 255)
        pdf_obj.set_text_color(255, 255, 255)
        pdf_obj.set_font("Arial", 'B', 8)
        pdf_obj.cell(15, 7, "Mes", 1, 0, 'C', fill=True)
        pdf_obj.cell(40, 7, "Renta Base", 1, 0, 'C', fill=True)
        pdf_obj.cell(35, 7, "IVA", 1, 0, 'C', fill=True)
        pdf_obj.cell(40, 7, "Pago Total", 1, 0, 'C', fill=True)
        pdf_obj.cell(60, 7, "Concepto", 1, 1, 'C', fill=True)
        pdf_obj.set_text_color(27, 27, 27)
        pdf_obj.set_font("Arial", '', 8)

    imprimir_encabezados_tabla(pdf)
    
    for _, row in df_comercial.iterrows():
        if pdf.get_y() > 265:
            pdf.add_page()
            imprimir_encabezados_tabla(pdf) 
            
        pdf.cell(15, 6, str(row['Mes']), 1, 0, 'C')
        pdf.cell(40, 6, row['Renta Base'], 1, 0, 'R')
        pdf.cell(35, 6, row['IVA'], 1, 0, 'R')
        pdf.cell(40, 6, row['Pago Total'], 1, 0, 'R')
        pdf.cell(60, 6, row['Concepto'], 1, 1, 'L')
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    st.markdown(f'<br><a href="data:application/pdf;base64,{b64_pdf}" download="TermSheet_FEX_{nombre_empresa}.pdf" style="padding:12px 20px; background-color:#0163FF; color:white; font-weight:bold; border-radius:4px; text-decoration:none; display:inline-block;">Descargar Archivo PDF</a>', unsafe_allow_html=True)
