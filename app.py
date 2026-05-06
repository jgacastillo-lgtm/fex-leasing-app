import streamlit as st
import numpy_financial as npf
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Cotizador FEX Capital", page_icon="🏢", layout="wide")

# 2. Motor Financiero
def calcular_escenario(moneda, precio, tasa_anual, meses, residual_porc, comision_porc):
    tasa_mensual = (tasa_anual / 100) / 12
    monto_residual = precio * (residual_porc / 100)
    
    renta_neta = abs(npf.pmt(tasa_mensual, meses, precio, -monto_residual, when=1))
    iva_renta = renta_neta * 0.16
    renta_total = renta_neta + iva_renta
    
    monto_comision = precio * (comision_porc / 100)
    pago_inicial = renta_total + monto_comision
    
    return renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual

# 3. Interfaz de Usuario (Panel Lateral)
st.sidebar.image("https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=500&auto=format&fit=crop&q=60", caption="FEX Capital Loans")
st.sidebar.header("⚙️ Parámetros del Arrendamiento")
moneda = st.sidebar.selectbox("Moneda", ["MXN", "USD"])
precio = st.sidebar.number_input("Precio del Equipo", min_value=10000, value=1000000, step=10000)
tasa = st.sidebar.slider("Tasa Anualizada (%)", 1.0, 50.0, 14.5, 0.5)
meses = st.sidebar.slider("Plazo (Meses)", 6, 72, 36, 6)
residual = st.sidebar.slider("Valor Residual (%)", 0, 50, 20, 1)
comision = st.sidebar.number_input("Comisión por Apertura (%)", min_value=0.0, value=2.0, step=0.5)

# 4. Cálculos
renta_neta, iva_renta, renta_total, monto_comision, pago_inicial, monto_residual = calcular_escenario(
    moneda, precio, tasa, meses, residual, comision
)

# 5. Visualización Principal
st.title("🏢 Simulador de Arrendamiento - FEX Capital")
st.markdown("---")

st.subheader("💰 Resumen Financiero")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Renta Mensual (Base)", f"${renta_neta:,.2f} {moneda}")
col2.metric("IVA (16%)", f"${iva_renta:,.2f} {moneda}")
col3.metric("Pago Total Mensual", f"${renta_total:,.2f} {moneda}")
col4.metric("Valor Residual Al Final", f"${monto_residual:,.2f} {moneda}")

st.info(f"**DESEMBOLSO INICIAL REQUERIDO:** ${pago_inicial:,.2f} {moneda} *(Incluye 1ra renta anticipada, IVA y {comision}% de comisión por apertura)*")

# 6. Tabla de Amortización
st.subheader("📊 Tabla de Amortización Proyectada")
datos_tabla = []
for mes in range(1, meses + 1):
    pago_efectivo = renta_total
    concepto = "Renta Mensual"
    if mes == 1:
        pago_efectivo += monto_comision
        concepto = "Renta 1 + Comisión Apertura"
        
    datos_tabla.append({
        "Mes": mes,
        f"Renta Base ({moneda})": round(renta_neta, 2),
        f"IVA ({moneda})": round(iva_renta, 2),
        f"Pago Total ({moneda})": round(pago_efectivo, 2),
        "Concepto": concepto
    })

st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True, hide_index=True)
