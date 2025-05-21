
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
import time

# ------------------ CONFIG ------------------

st.set_page_config(page_title="Radar de Tendências - Agronegócio", layout="wide")

st.markdown("<style>body { font-family: 'Segoe UI', sans-serif; }</style>", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------

st.sidebar.title("⚙️ Configurações do Radar")

uploaded_file = st.sidebar.file_uploader("📂 Enviar planilha Excel (.xlsx)", type=["xlsx"])

bg_image = st.sidebar.file_uploader("🖼️ Imagem de fundo (opcional)", type=["png", "jpg", "jpeg"])

font = st.sidebar.selectbox("🔤 Escolher fonte", ["Segoe UI", "Arial", "Courier New", "Georgia", "Verdana"])

speed = st.sidebar.slider("⏱️ Velocidade do ponteiro", 0.1, 2.0, 1.0, 0.1)

# ------------------ MAIN ------------------

st.title("📡 Radar de Tendências do Agronegócio (Estilo DHL)")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = {"Demanda", "Categoria", "Ocorrencias", "Maturidade", "PrazoEstimado", "NivelMaturidade"}
        if not required_columns.issubset(df.columns):
            st.error("A planilha deve conter as colunas: " + ", ".join(required_columns))
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

            # Anéis concêntricos
            for r in [25, 50, 75, 100]:
                fig.add_shape(type="circle", x0=-r, y0=-r, x1=r, y1=r,
                              xref="x", yref="y",
                              line=dict(color="lightgray", dash="dot"))

            # Linhas de setor
            for ang in np.arange(0, 360, setor_angulo):
                fig.add_shape(type="line",
                              x0=0, y0=0,
                              x1=100*np.cos(np.radians(ang)),
                              y1=100*np.sin(np.radians(ang)),
                              line=dict(color="lightgray", width=1))

            # Background
            if bg_image:
                img = Image.open(bg_image)
                fig.add_layout_image(
                    dict(
                        source=img,
                        xref="x", yref="y",
                        x=-100, y=100,
                        sizex=200, sizey=200,
                        xanchor="left", yanchor="top",
                        layer="below",
                        sizing="stretch"
                    )
                )

            # Ponteiro animado (simulado com tempo)
            t = time.time() * speed
            ponteiro_angulo = (t * 30) % 360  # gira em velocidade constante
            ponteiro_x = 90 * np.cos(np.radians(ponteiro_angulo))
            ponteiro_y = 90 * np.sin(np.radians(ponteiro_angulo))
            fig.add_shape(type="line",
                          x0=0, y0=0, x1=ponteiro_x, y1=ponteiro_y,
                          line=dict(color="red", width=3))

            # Plotar demandas
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
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="white",
                title="Radar de Tendências",
                font=dict(family=font, size=14)
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("Envie uma planilha para começar...")
