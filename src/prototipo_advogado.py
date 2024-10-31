import json
import locale

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

with open("dados_advogado.json", "r") as file:
    json_data = file.read()

json_dict = json.loads(json_data)
primeira_chave = next(iter(json_dict))
processos = json_dict[primeira_chave]
df = pd.json_normalize(processos)

# ========================== Indicadores Gerais ==========================
# Filtrar processos que tenham a OAB 'uf = SP' e 'numero = 492370'
uf_alvo = "SP"
numero_oab_alvo = 492370

total_processos = len(df)
qtd_polo_ativo = len(
    df[
        df["partes"].apply(
            lambda partes: any(
                p.get("polo") == "ATIVO"
                and any(
                    adv.get("oab", {}).get("uf") == uf_alvo
                    and adv.get("oab", {}).get("numero") == numero_oab_alvo
                    for adv in p.get("advogados", [])
                )
                for p in partes
            )
        )
    ]
)
qtd_polo_passivo = len(
    df[
        df["partes"].apply(
            lambda partes: any(
                p.get("polo") == "PASSIVO"
                and any(
                    adv.get("oab", {}).get("uf") == uf_alvo
                    and adv.get("oab", {}).get("numero") == numero_oab_alvo
                    for adv in p.get("advogados", [])
                )
                for p in partes
            )
        )
    ]
)

# Valor total de causa e valores por polo considerando a OAB alvo
valor_total = df["valorCausa.valor"].sum()
valor_ativo = df[
    df["partes"].apply(
        lambda partes: any(
            p.get("polo") == "ATIVO"
            and any(
                adv.get("oab", {}).get("uf") == uf_alvo
                and adv.get("oab", {}).get("numero") == numero_oab_alvo
                for adv in p.get("advogados", [])
            )
            for p in partes
        )
    )
]["valorCausa.valor"].sum()
valor_passivo = df[
    df["partes"].apply(
        lambda partes: any(
            p.get("polo") == "PASSIVO"
            and any(
                adv.get("oab", {}).get("uf") == uf_alvo
                and adv.get("oab", {}).get("numero") == numero_oab_alvo
                for adv in p.get("advogados", [])
            )
            for p in partes
        )
    )
]["valorCausa.valor"].sum()

# Média de valor de execução considerando a OAB alvo
valor_execucao = df["statusPredictus.valorExecucao.valor"].sum()
valor_execucao_ativo = df[
    df["partes"].apply(
        lambda partes: any(
            p.get("polo") == "ATIVO"
            and any(
                adv.get("oab", {}).get("uf") == uf_alvo
                and adv.get("oab", {}).get("numero") == numero_oab_alvo
                for adv in p.get("advogados", [])
            )
            for p in partes
        )
    )
]["statusPredictus.valorExecucao.valor"].sum()
valor_execucao_passivo = df[
    df["partes"].apply(
        lambda partes: any(
            p.get("polo") == "PASSIVO"
            and any(
                adv.get("oab", {}).get("uf") == uf_alvo
                and adv.get("oab", {}).get("numero") == numero_oab_alvo
                for adv in p.get("advogados", [])
            )
            for p in partes
        )
    )
]["statusPredictus.valorExecucao.valor"].sum()

# ========================== Distribuições ==========================
# Distribuição por Tipo de Julgamento
df_julgamentos = df["statusPredictus.julgamentos"].explode().dropna().apply(pd.Series)
distribuicao_tipo_julgamento = (
    df_julgamentos["tipoJulgamento"].value_counts().reset_index()
)
distribuicao_tipo_julgamento.columns = ["Categoria", "Total"]

# Distribuição por Ramo do Direito
distribuicao_ramo_direito = (
    df["statusPredictus.ramoDireito"].value_counts().reset_index()
)
distribuicao_ramo_direito.columns = ["Categoria", "Total"]

# Distribuição por Status dos Processos
distribuicao_status_processos = (
    df["statusPredictus.statusProcesso"].value_counts().reset_index()
)
distribuicao_status_processos.columns = ["Categoria", "Total"]

# Distribuiçã por tribunal
distribuicao_tribunal = df["tribunal"].value_counts().reset_index()
distribuicao_tribunal.columns = ["Tribunal", "Total"]

# ========================== Rankings ==========================
classes = df["classeProcessual.nome"].value_counts().reset_index()
classes.columns = ["Classe Processual", "Total"]

# Top 5 principais assuntos principais
assuntos_principais = (
    df["assuntosCNJ"]
    .explode()
    .apply(
        lambda x: (
            x["titulo"] if isinstance(x, dict) and x.get("ePrincipal", False) else None
        )
    )
    .dropna()
    .value_counts()
    .reset_index()
)
assuntos_principais.columns = ["Assunto", "Total"]

# Top 5 principais representados por Polo Ativo e Polo Passivo
df_partes = df["partes"].explode().apply(pd.Series)

# Filtrando partes com advogado alvo
df_partes_ativo_adv = (
    df_partes[df_partes["polo"] == "ATIVO"]
    .explode("advogados")
    .dropna(subset=["advogados"])
)
df_partes_ativo_adv = df_partes_ativo_adv[
    df_partes_ativo_adv["advogados"].apply(
        lambda adv: isinstance(adv, dict)
        and adv.get("oab", {}).get("uf") == uf_alvo
        and adv.get("oab", {}).get("numero") == numero_oab_alvo
    )
].reset_index(drop=True)
df_partes_ativo_adv = df_partes_ativo_adv[
    df_partes_ativo_adv["advogados"].apply(
        lambda adv: adv.get("oab", {}).get("uf") == uf_alvo
        and adv.get("oab", {}).get("numero") == numero_oab_alvo
    )
].reset_index(drop=True)
df_partes_passivo_adv = (
    df_partes[df_partes["polo"] == "PASSIVO"]
    .explode("advogados")
    .dropna(subset=["advogados"])
)
df_partes_passivo_adv = df_partes_passivo_adv[
    df_partes_passivo_adv["advogados"].apply(
        lambda adv: isinstance(adv, dict)
        and adv.get("oab", {}).get("uf") == uf_alvo
        and adv.get("oab", {}).get("numero") == numero_oab_alvo
    )
].reset_index(drop=True)
df_partes_passivo_adv = df_partes_passivo_adv[
    df_partes_passivo_adv["advogados"].apply(
        lambda adv: adv.get("oab", {}).get("uf") == uf_alvo
        and adv.get("oab", {}).get("numero") == numero_oab_alvo
    )
].reset_index(drop=True)

top_5_representados_ativo = df_partes_ativo_adv["nome"].value_counts().head(5)
top_5_representados_passivo = df_partes_passivo_adv["nome"].value_counts().head(5)

# ========================== Dados para Mapa ==========================
df_estados = (
    df.groupby("uf")
    .agg(
        quantidade=("numeroProcessoUnico", "count"),
        valor_total=("valorCausa.valor", "sum"),
    )
    .reset_index()
)

df_estados["percentual"] = (
    df_estados["quantidade"] / df_estados["quantidade"].sum()
) * 100

# ========================== Streamlit ==========================
st.set_page_config(
    layout="wide", page_title="Visão Geral da Plataforma - Advogado", page_icon="📊"
)
st.title("Visão Geral da Plataforma - Advogado")
st.markdown("---")
col1, col2, col3 = st.columns(3)


def format_currency(value):
    return f"R$ {locale.format_string('%.2f', value, grouping=True)}"


# Card for Process Counts
with col1:
    with st.container(border=1):
        st.markdown(
            f"<h1 style='color: #21332C;'>{total_processos:n}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("Processos encontrados")
        st.markdown(f"{qtd_polo_ativo:n} como autor")
        st.progress(qtd_polo_ativo / total_processos)
        st.markdown(f"{qtd_polo_passivo:n} como réu")
        st.progress(qtd_polo_passivo / total_processos)

# Card for Valor das Causas
with col2:
    with st.container(border=1):
        st.markdown(
            f"<h1 style='color: #21332C;'>{format_currency(valor_total)}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("Valor das causas")
        st.markdown(f"{format_currency(valor_ativo)} como autor")
        st.progress(valor_ativo / valor_total)
        st.markdown(f"{format_currency(valor_passivo)} como réu")
        st.progress(valor_passivo / valor_total)

# Card for Valor das Execuções
with col3:
    with st.container(border=1):
        st.markdown(
            f"<h1 style='color: #21332C;'>{format_currency(valor_execucao)}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("Valor das execuções")
        st.markdown(f"{format_currency(valor_execucao_ativo)} como autor")
        percentage = valor_execucao_ativo / valor_execucao
        st.progress(percentage if percentage > 0 else 0)
        st.markdown(f"{format_currency(valor_execucao_passivo)} como réu")
        percentage = valor_execucao_passivo / valor_execucao
        st.progress(percentage if percentage > 0 else 0)

with col1:
    with st.container(border=1, height=500):
        st.subheader("Distribuição por Status do Processo")
        grafico_barras_horizontais = px.bar(
            distribuicao_status_processos,
            x="Total",
            y="Categoria",
            text="Total",
            orientation="h",
            color_discrete_sequence=["#45A874"],
            labels={"Categoria": "", "Total": ""},
        )
        st.plotly_chart(grafico_barras_horizontais, use_container_width=True)

# Card de Processos por Ramo do Direito
with col2:
    with st.container(border=1, height=500):
        st.subheader("Distribuição por Ramo do Direito")
        grafico_barras_verticais = px.bar(
            distribuicao_ramo_direito,
            x="Categoria",
            y="Total",
            text="Total",
            color_discrete_sequence=["#45A874"],
            labels={"Categoria": "", "Total": ""},
        )
        st.plotly_chart(grafico_barras_verticais, use_container_width=True)

with col3:
    with st.container(border=1, height=500):
        st.subheader("Distribuição por Tribunal")
        grafico_barras_verticais = px.bar(
            distribuicao_tribunal,
            x="Tribunal",
            y="Total",
            text="Total",
            color_discrete_sequence=["#45A874"],
            labels={"Tribunal": "", "Total": ""},
        )
        st.plotly_chart(grafico_barras_verticais, use_container_width=True)

# Mapa de processos por UF
df_estados = (
    df.groupby("uf")
    .agg(
        quantidade=("numeroProcessoUnico", "count"),
        valor_total=("valorCausa.valor", "sum"),
    )
    .reset_index()
)
df_estados["percentual"] = (
    df_estados["quantidade"] / df_estados["quantidade"].sum()
) * 100
estados_brasil = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
response = requests.get(geojson_url)
geojson_brasil = response.json()
df_estado_completo = pd.DataFrame(estados_brasil, columns=["uf"])
df_estado_completo = df_estado_completo.merge(df_estados, on="uf", how="left").fillna(
    {"quantidade": 0, "percentual": 0, "valor_total": 0}
)
df_estado_completo["Label"] = df_estado_completo.apply(
    lambda row: f"{row['uf']}: {row['quantidade']} processos ({row['percentual']:.2f}%)",
    axis=1,
)

col1, col2 = st.columns([3, 2])

with col1:
    with st.container(border=1, height=500):
        st.subheader("Distribuição por UF")
        mapa = px.choropleth(
            df_estado_completo,
            geojson=geojson_brasil,
            locations="uf",
            featureidkey="properties.sigla",
            color="quantidade",
            hover_name="Label",
            color_continuous_scale=[
                "rgba(69, 168, 116, 0.1)",  # Verde claro para valores baixos
                "#45A874",  # Verde médio
                "#2A4C3F",  # Verde escuro
                "#21332C",  # Verde ainda mais escuro
            ],
        )
        mapa.update_geos(
            fitbounds="locations",
            visible=True,
            showcoastlines=False,
            showcountries=False,
        )
        mapa.update_traces(marker_line_width=0.5, text=df_estado_completo["Label"])
        st.plotly_chart(mapa, use_container_width=True)

with col2:
    with st.container(border=1, height=500):
        st.subheader("Distribuição por Status do Processo")
        grafico_barras_horizontais = px.bar(
            distribuicao_tipo_julgamento,
            x="Total",
            y="Categoria",
            text="Total",
            orientation="h",
            color_discrete_sequence=["#45A874"],
            labels={"Categoria": "", "Total": ""},
        )
        st.plotly_chart(grafico_barras_horizontais, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=1, height=300):
        st.subheader("Distribuição de Assuntos Principais")
        st.dataframe(assuntos_principais, height=300, width=750, hide_index=True)

with col2:
    with st.container(border=1, height=300):
        st.subheader("Distribuição de Classes Processuais")
        st.dataframe(classes, height=300, width=750, hide_index=True)

top_5_envolvidos_ativo = df_partes_ativo_adv["nome"].value_counts().head(5)
top_5_envolvidos_ativo = top_5_envolvidos_ativo.reset_index()
top_5_envolvidos_ativo.columns = ["Parte", "Total"]
top_5_envolvidos_ativo.index = top_5_envolvidos_ativo.index + 1

with col1:
    with st.container(border=1, height=300):
        st.subheader("Top 5 Partes - Polo Ativo")
        st.dataframe(
            top_5_envolvidos_ativo,
            height=300,
            width=750,
        )

top_5_envolvidos_passivo = df_partes_passivo_adv["nome"].value_counts().head(5)
top_5_envolvidos_passivo = top_5_envolvidos_passivo.reset_index()
top_5_envolvidos_passivo.columns = ["Parte", "Total"]
top_5_envolvidos_passivo.index = top_5_envolvidos_passivo.index + 1

with col2:
    with st.container(border=1, height=300):
        st.subheader("Top 5 Partes - Polo Passivo")
        st.dataframe(
            top_5_envolvidos_passivo,
            height=300,
            width=750,
        )

top_5_representados_ativo = top_5_representados_ativo.reset_index()
top_5_representados_ativo.columns = ["Parte", "Total"]
top_5_representados_ativo.index = top_5_representados_ativo.index + 1

with col1:
    with st.container(border=1, height=300):
        st.subheader("Top 5 Representados - Polo Ativo")
        st.dataframe(
            top_5_representados_ativo,
            height=300,
            width=750,
        )

top_5_representados_passivo = top_5_representados_passivo.reset_index()
top_5_representados_passivo.columns = ["Parte", "Total"]
top_5_representados_passivo.index = top_5_representados_passivo.index + 1

with col2:
    with st.container(border=1, height=300):
        st.subheader("Top 5 Representados - Polo Passivo")
        st.dataframe(
            top_5_representados_passivo,
            height=300,
            width=750,
        )
