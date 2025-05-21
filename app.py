
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Radar de Demandas - Agronegócio", layout="wide")

st.title("📡 Radar de Tendências do Agronegócio (Estilo DHL)")
st.markdown("Faça o upload de uma planilha Excel com os campos: **Demanda, Categoria, Ocorrencias, Maturidade, PrazoEstimado, NivelMaturidade**")

uploaded_file = st.file_uploader("📂 Envie sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Validar colunas esperadas
        colunas_esperadas = {"Demanda", "Categoria", "Ocorrencias", "Maturidade", "PrazoEstimado", "NivelMaturidade"}
        if not colunas_esperadas.issubset(df.columns):
            st.error("A planilha deve conter as colunas: " + ", ".join(colunas_esperadas))
        else:
            categorias = df["Categoria"].unique()
            n_setores = len(categorias)
            setor_angulo = 360 / n_setores
            categoria_to_angulo_base = {cat: i * setor_angulo for i, cat in enumerate(categorias)}

            df["setor_base"] = df["Categoria"].map(categoria_to_angulo_base)
            df["offset"] = df.groupby("Categoria").cumcount()
            df["angulo"] = df["setor_base"] + df["offset"] * (setor_angulo / 5)

            nivel_para_raio = {1: 25, 2: 50, 3: 75}
            df["raio"] = df["NivelMaturidade"].map(nivel_para_raio)

            df["x"] = df["raio"] * np.cos(np.radians(df["angulo"]))
            df["y"] = df["raio"] * np.sin(np.radians(df["angulo"]))

            fig = go.Figure()

            for r in [25, 50, 75, 100]:
                fig.add_shape(type="circle", x0=-r, y0=-r, x1=r, y1=r,
                              xref="x", yref="y", line=dict(color="lightgray", dash="dot"))

            for ang in np.arange(0, 360, setor_angulo):
                fig.add_shape(type="line", x0=0, y0=0,
                              x1=100*np.cos(np.radians(ang)), y1=100*np.sin(np.radians(ang)),
                              line=dict(color="lightgray", width=1))

            for cat in categorias:
                sub = df[df["Categoria"] == cat]
                fig.add_trace(go.Scatter(
                    x=sub["x"], y=sub["y"],
                    mode="markers+text",
                    marker=dict(size=16),
                    name=cat,
                    text=sub["Demanda"],
                    textposition="top center",
                    hovertemplate=
                    "<b>%{text}</b><br>" +
                    "Categoria: %{customdata[0]}<br>" +
                    "Maturidade: %{customdata[1]}<br>" +
                    "Prazo: %{customdata[2]}<br>" +
                    "Ocorrencias: %{customdata[3]}<br>",
                    customdata=sub[["Categoria", "Maturidade", "PrazoEstimado", "Ocorrencias"]]
                ))

            fig.update_layout(
                width=900,
                height=900,
                showlegend=True,
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                plot_bgcolor="white",
                title="Radar de Tendências"
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
else:
    st.info("Aguardando envio da planilha...")

