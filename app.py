import streamlit as st
import numpy_financial as npf
import pandas as pd
from fpdf import FPDF
import base64
import os
from datetime import datetime

# 1. Configuracion de pagina
st.set_page_config(page_title="FEX Capital - Calculadora de Arrendamiento", layout="wide")

LOGO_PATH = "LOGO FEX.png"

# 2. Clase para PDF
class TermSheetPDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=80, y=10, w=50)
        self.set_y(38)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(27, 27, 27) 
        # CAMBIO APLICADO AQUÍ: Nuevo título del documento
        self.cell(0, 6, 'Cotizacion Arrendamiento Puro', 0, 1, 'C')
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        self.set_font('Arial', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Fecha: {fecha_hoy}', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# 3. Motor Financiero Desglosado
def calcular_escenario(precio_con_iva, tasa_anual, meses, residual_porc, comision_porc):
    precio_base = precio_con_iva / 1.16
    tasa_mensual = (tasa_anual / 100) / 12
    
    monto_residual = precio_base * (residual_porc / 100)
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio_base, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    comision_neta = precio_base * (comision_porc / 100)
    comision_iva = comision_neta * 0.16
    comision_total = comision_neta + comision_iva
    
    pago_inicial_neto = renta_neta + comision_neta + renta_neta
    pago_inicial_iva = iva_renta + comision_iva + iva_renta
    pago_inicial_total = renta_total + comision_total + renta_total
    
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
    
st.sidebar.markdown("### Configuracion de Parametros")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio_input = st.sidebar.number_input("Precio del Equipo (IVA incluido)", min_value=1000.0, value=307986.96, step=10000.0, format="%.2f")
tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo Forzoso (Meses)", 6, 72, 36, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 10, 1)
comision = st.sidebar.number_input("Comision por Apertura (%)", min_value=0.0, value=3.0, step=0.5, format="%.2f")

# 5. Captura Datos
st.title("Calculadora de Arrendamiento")
st.markdown("---")

with st.expander("Informacion Legal del Cliente", expanded=True):
    c_c1, c_c2 = st.columns(2)
    nombre_empresa = c_c1.text_input("Razon Social / Empresa", "MAREA ALIMENTOS")
    rfc_cliente = c_c1.text_input("RFC", "MAL221117ANO")
    representante = c_c2.text_input("Representante Legal", "Nombre del Representante")
    
    descripcion_default = "19x Smart Store 600 Duo Mexico\n19x PAX IM30 Kit\n19x Complete Roller Set para Smart Store"
    equipo_desc = st.text_area("Descripcion detallada del Activo", descripcion_default, height=100)

# Ejecucion de Calculos
vals = calcular_escenario(precio_input, tasa, meses, residual, comision)

# 6. Resumen de Condiciones (Web)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Resumen de la Operacion")

df_firma = pd.DataFrame({
    "Concepto": ["1era Renta Anticipada", "Comision por Apertura", "Renta en Garantia", "TOTAL A LA FIRMA"],
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
    "Concepto": ["Valor de mercado estimado al vencimiento"],
    "Valor Neto": [f"{moneda} ${vals['residual_neto']:,.2f}"],
    "I.V.A.": [f"{moneda} ${vals['residual_iva']:,.2f}"],
    "Valor Total": [f"{moneda} ${vals['residual_total']:,.2f}"]
})

st.markdown("**A la firma del contrato se pagara:**")
st.dataframe(df_firma, use_container_width=True, hide_index=True)

st.markdown("**Mensualidades:**")
st.dataframe(df_mensualidades, use_container_width=True, hide_index=True)

st.markdown("**Al termino del contrato:**")
st.dataframe(df_termino, use_container_width=True, hide_index=True)

with st.expander("Vista Analitica Interna (Exclusivo FEX Capital)"):
    # TIR (IRR)
    flujos_efectivo = [-vals['precio_base'] + vals['renta_neta'] + vals['comision_neta'] + vals['renta_neta']]
    for _ in range(meses - 2):
        flujos_efectivo.append(vals['renta_neta'])
    flujos_efectivo.append(vals['residual_neto'])
    tir_mensual = npf.irr(flujos_efectivo)
    tir_anual = tir_mensual * 12 * 100
    
    col1, col2 = st.columns(2)
    col1.info(f"Monto a Financiar (Base sin IVA): {moneda} ${vals['precio_base']:,.2f}")
    col2.success(f"TIR Anualizada (IRR) de la Operacion: {tir_anual:.2f}%")
    
    datos_internos = []
    saldo_insoluto = vals['precio_base']
    for mes in range(1, meses + 1):
        interes_mes = 0 if mes == 1 else saldo_insoluto * vals['tasa_mensual']
        capital_mes = vals['renta_neta'] - interes_mes
        saldo_insoluto -= capital_mes
        datos_internos.append({
            "Mes": mes,
            "Renta (sin IVA)": vals['renta_neta'],
            "Interes": interes_mes,
            "Amortizacion Capital": capital_mes,
            "Saldo Insoluto": max(saldo_insoluto, 0)
        })
    st.dataframe(pd.DataFrame(datos_internos).style.format({
        "Renta (sin IVA)": "{:,.2f}", "Interes": "{:,.2f}", "Amortizacion Capital": "{:,.2f}", "Saldo Insoluto": "{:,.2f}"
    }), use_container_width=True)

# 7. Boton PDF
st.markdown("---")
if st.button("Generar y Descargar Cotizacion PDF"):
    pdf = TermSheetPDF()
    pdf.add_page()
    pdf.set_text_color(27, 27, 27)
    
    # 1. INFORMACION GENERAL
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. INFORMACION GENERAL", ln=True, border='B')
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 7, f"Cliente: {nombre_empresa}", 0, 0)
    pdf.cell(95, 7, f"RFC: {rfc_cliente}", 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 7, "Activo:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, equipo_desc)
    
    pdf.cell(0, 7, f"Valor del Activo (IVA inc): {moneda} ${precio_input:,.2f}", ln=True)
    pdf.ln(5)

    # 2. A LA FIRMA
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
    
    pdf.cell(190, 2, "", "B", 1) 
    pdf.ln(1); pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 6, "TOTALES :", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['pago_inicial_neto']:,.2f}", 0, 0, 'R'); pdf.cell(38, 6, f"{vals['pago_inicial_iva']:,.2f}", 0, 0, 'R'); pdf.cell(39, 6, f"{vals['pago_inicial_total']:,.2f}", 0, 1, 'R')
    pdf.ln(5)

    # 3. MENSUALIDADES
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

    # 4. AL TERMINO
    pdf.set_fill_color(210, 210, 210)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "Al termino del contrato", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 7, "Valor de mercado estimado al vencimiento:", 0, 0, 'R'); pdf.cell(38, 7, f"{vals['residual_neto']:,.2f}", 0, 0, 'R'); pdf.cell(38, 7, f"{vals['residual_iva']:,.2f}", 0, 0, 'R'); pdf.cell(39, 7, f"{vals['residual_total']:,.2f}", 0, 1, 'R')
    
    # 5. NOTAS LEGALES (PIE DE PAGINA)
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "1) La renta es fija y se paga al inicio de cada periodo.", ln=True)
    pdf.cell(0, 5, "2) Esta cotizacion requiere autorizacion del Comite de Credito.", ln=True)
    pdf.cell(0, 5, "3) Los precios son sujetos a cambio sin previo aviso.", ln=True)
    pdf.cell(0, 5, f"4) La moneda de esta cotizacion es: {moneda}", ln=True)
    pdf.cell(0, 5, "5) La renta en garantia pagada al inicio, se utilizara para cubrir la ultima renta.", ln=True)
    pdf.cell(0, 5, "6) El valor del mercado estimado no representa ningun compromiso de compra venta entre las partes.", ln=True)

    # FIRMAS
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 10, "__________________________________", 0, 0, 'C'); pdf.cell(90, 10, "__________________________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C'); pdf.cell(90, 5, "Por: FEX CAPITAL, S.A. DE C.V.", 0, 1, 'C')
    pdf.cell(90, 5, f"{representante}", 0, 0, 'C'); pdf.cell(90, 5, "Representante Legal", 0, 1, 'C')
    
    # Generar descarga
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    st.markdown(f'<br><a href="data:application/pdf;base64,{b64_pdf}" download="Cotizacion_FEX_{nombre_empresa}.pdf" style="padding:12px 20px; background-color:#0163FF; color:white; font-weight:bold; border-radius:4px; text-decoration:none; display:inline-block;">Descargar Cotizacion PDF</a>', unsafe_allow_html=True)
