import streamlit as st
import numpy_financial as npf
import pandas as pd
from fpdf import FPDF
import base64

# 1. Configuración
st.set_page_config(page_title="FEX Capital - Cotizador Pro", page_icon="🏢", layout="wide")

# 2. Clase para PDF (Tabla Comercial)
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

# 3. Motor Financiero con Desglose de IVA
def calcular_escenario(precio_con_iva, tasa_anual, meses, residual_porc, comision_porc):
    # Desglosamos el IVA para obtener el monto real a financiar
    precio_base = precio_con_iva / 1.16
    tasa_mensual = (tasa_anual / 100) / 12
    monto_residual = precio_base * (residual_porc / 100)
    
    # Renta Anticipada sobre el precio base
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio_base, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    # Comisión sobre el monto base
    monto_comision = precio_base * (comision_porc / 100)
    pago_inicial = renta_total + monto_comision
    
    return precio_base, renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual, tasa_mensual

# 4. Interfaz Lateral
st.sidebar.header("⚙️ Configuración")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio_input = st.sidebar.number_input("Precio del Equipo (IVA incluido)", min_value=1000, value=1160000)
tasa = st.sidebar.slider("Tasa Anual (%)", 1.0, 100.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo (Meses)", 6, 72, 24, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 40, 0, 1)
comision = st.sidebar.number_input("Comisión Apertura (%)", min_value=0.0, value=2.0, step=0.5)

# 5. Captura Datos
st.title("🏢 Sistema de Cotización FEX Capital")
with st.expander("📝 Datos del Cliente", expanded=True):
    c_c1, c_c2 = st.columns(2)
    nombre_empresa = c_c1.text_input("Empresa", "SEPRINAL")
    rfc_cliente = c_c1.text_input("RFC", "ABC123456XYZ")
    representante = c_c2.text_input("Representante", "Juanito Caminador")
    equipo_desc = c_c2.text_input("Activo", "Equipo de Transporte")

# Cálculos
p_base, r_neta, i_renta, r_total, m_comision, p_inicial, m_residual, t_mensual = calcular_escenario(
    precio_input, tasa, meses, residual, comision
)

# 6. Resumen
st.markdown("---")
res1, res2, res3 = st.columns(3)
res1.metric("Renta Mensual Total", f"{moneda} ${r_total:,.2f}")
res2.metric("Pago Inicial", f"{moneda} ${p_inicial:,.2f}")
res3.metric("Valor Residual", f"{moneda} ${m_residual:,.2f}")

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
        "Concepto": "1ra Renta + Comisión" if mes == 1 else "Renta Mensual"
    })
    
    datos_internos.append({
        "Mes": mes,
        "Renta (sin IVA)": r_neta,
        "Interés": interes_mes,
        "Amort. Capital": capital_mes,
        "Saldo Insoluto": max(saldo_insoluto, 0)
    })

df_comercial = pd.DataFrame(datos_comerciales)
df_interno = pd.DataFrame(datos_internos)

# Vista Web
st.subheader("📊 Proyección Comercial (Cliente)")
st.dataframe(df_comercial, use_container_width=True, hide_index=True)

with st.expander("🛠️ VISTA INTERNA (Sólo FEX Capital)"):
    st.info(f"Precio Base desglosado: {moneda} ${p_base:,.2f}")
    st.dataframe(df_interno.style.format({
        "Renta (sin IVA)": "{:,.2f}", "Interés": "{:,.2f}", "Amort. Capital": "{:,.2f}", "Saldo Insoluto": "{:,.2f}"
    }), use_container_width=True)

# 8. Botón PDF
if st.button("🚀 Descargar Term Sheet"):
    pdf = TermSheetPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "1. DATOS DEL CLIENTE", ln=True, border='B')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Empresa: {nombre_empresa}", ln=True); pdf.cell(0, 8, f"RFC: {rfc_cliente}", ln=True)
    pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "2. CONDICIONES", ln=True, border='B')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Activo: {equipo_desc}", ln=True); pdf.cell(0, 8, f"Plazo: {meses} meses", ln=True)
    pdf.cell(0, 8, f"Precio Total Equipo (Ref): {moneda} ${precio_input:,.2f}", ln=True)
    pdf.ln(5); pdf.set_fill_color(230, 240, 255); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f"TOTAL A PAGAR AL FIRMAR: {moneda} ${p_inicial:,.2f}", ln=True, fill=True, align='C')
    pdf.ln(10); pdf.cell(90, 10, "________________", 0, 0, 'C'); pdf.cell(90, 10, "________________", 0, 1, 'C')
    pdf.cell(90, 5, f"Por: {nombre_empresa}", 0, 0, 'C'); pdf.cell(90, 5, "Por: FEX CAPITAL", 0, 1, 'C')
    
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "ANEXO A: TABLA DE PAGOS", ln=True, border='B'); pdf.ln(5)
    pdf.set_font("Arial", 'B', 8)
    for c in ["Mes", "Renta Base", "IVA", "Pago Total", "Concepto"]: pdf.cell(38 if c != "Mes" else 15, 7, c, 1)
    pdf.ln()
    pdf.set_font("Arial", '', 8)
    for _, row in df_comercial.iterrows():
        pdf.cell(15, 6, str(row['Mes']), 1)
        pdf.cell(38, 6, row['Renta Base'], 1); pdf.cell(38, 6, row['IVA'], 1); pdf.cell(38, 6, row['Pago Total'], 1); pdf.cell(38, 6, row['Concepto'], 1, 1)
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
    st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="FEX_{nombre_empresa}.pdf" style="padding:10px; background:#2980b9; color:white; border-radius:5px; text-decoration:none;">📥 Descargar PDF</a>', unsafe_allow_html=True)
