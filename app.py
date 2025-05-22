
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image
import time

st.set_page_config(page_title="Radar Agro Club Tecnológico", layout="wide")
st.markdown("<style>body { font-family: 'Segoe UI', sans-serif; }</style>", unsafe_allow_html=True)

st.title("🌾 Radar Agro Club Tecnológico")

# Sidebar com filtros e configurações visuais
st.sidebar.header("⚙️ Configurações Visuais e Filtros")

uploaded_file = st.sidebar.file_uploader("📂 Enviar planilha Excel (.xlsx)", type=["xlsx"])
bg_image = st.sidebar.file_uploader("🖼️ Imagem de fundo (opcional)", type=["png", "jpg", "jpeg"])
font = st.sidebar.selectbox("🔤 Fonte", ["Segoe UI", "Arial", "Courier New", "Georgia", "Verdana"])
radar_size = st.sidebar.slider("📏 Tamanho do radar", 600, 1200, 900, 100)
speed = st.sidebar.slider("⏱️ Velocidade do ponteiro", 0.1, 3.0, 1.0, 0.1)
font_color = st.sidebar.color_picker("🎨 Cor da fonte", "#000000")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        required_cols = {"Categoria", "Demanda", "Aderência", "PrazoEstimado", "EstadoRegiao", "Aderencia_%", "NivelMaturidade"}
        if not required_cols.issubset(df.columns):
            st.error("A planilha deve conter as colunas: " + ", ".join(required_cols))
        else:
            # Filtros interativos
            categoria_sel = st.sidebar.multiselect("🔎 Categoria", sorted(df["Categoria"].unique()), default=list(df["Categoria"].unique()))
            demanda_sel = st.sidebar.multiselect("📌 Demanda", sorted(df["Demanda"].unique()), default=list(df["Demanda"].unique()))
            regiao_sel = st.sidebar.multiselect("🗺️ Estado/Região", sorted(df["EstadoRegiao"].unique()), default=list(df["EstadoRegiao"].unique()))

            df = df[
                df["Categoria"].isin(categoria_sel) &
                df["Demanda"].isin(demanda_sel) &
                df["EstadoRegiao"].isin(regiao_sel)
            ]

            categorias = df["Categoria"].unique()
            n_setores = len(categorias)
            setor_angulo = 360 / n_setores if n_setores > 0 else 360
            categoria_to_angulo_base = {cat: i * setor_angulo for i, cat in enumerate(categorias)}

            df["setor_base"] = df["Categoria"].map(categoria_to_angulo_base)
            df["offset"] = df.groupby("Categoria").cumcount()
            df["angulo"] = df["setor_base"] + df["offset"] * (setor_angulo / 5)
            df["raio"] = df["NivelMaturidade"].apply(lambda x: 25 if x == 1 else (50 if x == 2 else 75))

            df["x"] = df["raio"] * np.cos(np.radians(df["angulo"]))
            df["y"] = df["raio"] * np.sin(np.radians(df["angulo"]))

            fig = go.Figure()

            for r in [25, 50, 75, 100]:
                fig.add_shape(type="circle", x0=-r, y0=-r, x1=r, y1=r,
                              xref="x", yref="y",
                              line=dict(color="#dddddd", dash="dot"))

            for ang in np.arange(0, 360, setor_angulo):
                fig.add_shape(type="line",
                              x0=0, y0=0,
                              x1=100*np.cos(np.radians(ang)),
                              y1=100*np.sin(np.radians(ang)),
                              line=dict(color="#eeeeee", width=1))

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

            # Ponteiro giratório
            t = time.time() * speed
            ponteiro_angulo = (t * 30) % 360
            ponteiro_x = 90 * np.cos(np.radians(ponteiro_angulo))
            ponteiro_y = 90 * np.sin(np.radians(ponteiro_angulo))
            fig.add_shape(type="line",
                          x0=0, y0=0, x1=ponteiro_x, y1=ponteiro_y,
                          line=dict(color="red", width=3))

            for cat in categorias:
                sub = df[df["Categoria"] == cat]
                fig.add_trace(go.Scatter(
                    x=sub["x"], y=sub["y"],
                    mode="markers+text",
                    marker=dict(size=16, color="rgba(0,123,255,0.7)", line=dict(color="white", width=1)),
                    name=cat,
                    text=sub["Demanda"],
                    textposition="top center",
                    hovertemplate=
                    "<b>%{text}</b><br>" +
                    "Categoria: %{customdata[0]}<br>" +
                    "Aderência: %{customdata[1]}<br>" +
                    "Maturidade: %{customdata[2]}<br>" +
                    "Prazo: %{customdata[3]}<br>" +
                    "Região: %{customdata[4]}<br>",
                    textfont=dict(color=font_color),
                    customdata=sub[["Categoria", "Aderência", "NivelMaturidade", "PrazoEstimado", "EstadoRegiao"]]
                ))

            fig.update_layout(
                width=radar_size,
                height=radar_size,
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="white",
                title="Radar Agro Club Tecnológico",
                font=dict(family=font, color=font_color, size=14),
                margin=dict(l=0, r=0, t=40, b=0)
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
else:
    st.info("Faça upload de uma planilha para começar.")
