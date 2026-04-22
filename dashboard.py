import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NBA Dashboard", layout="wide")

@st.cache_data
def load_data(path="nba_all_elo.csv"):
    df = pd.read_csv(path, dtype=str)  
    
    rename_map = {
        "year_id": "season",
        "team_id": "team",
        "date_game": "game_date",
        "seasongame": "seasongame",
        "is_playoffs": "is_playoffs",
        "game_result": "game_result"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
   
    if "season" in df.columns:
        df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    if "seasongame" in df.columns:
        df["seasongame"] = pd.to_numeric(df["seasongame"], errors="coerce").astype("Int64")
    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce", dayfirst=False)
    if "is_playoffs" in df.columns:
        df["is_playoffs"] = pd.to_numeric(df["is_playoffs"], errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=[c for c in ["team", "game_result", "season"] if c in df.columns])
    df["type"] = df["is_playoffs"].apply(lambda x: "Playoffs" if int(x) == 1 else "Temporada regular")
    df["game_result"] = df["game_result"].str.strip().str.upper().where(df["game_result"].notna())
    df = df[df["game_result"].isin(["W", "L"])]
    return df

df = load_data()


st.sidebar.header("Filtros")
years = sorted(df["season"].dropna().unique())
years = [int(y) for y in years]
selected_year = st.sidebar.selectbox("Selecciona un año", years, index=len(years)-1)

teams = sorted(df[df["season"] == selected_year]["team"].unique())
if not teams:
    teams = sorted(df["team"].unique())
selected_team = st.sidebar.selectbox("Selecciona un equipo", teams)

game_type = st.sidebar.radio(
    "Selecciona tipo de juego",
    options=["Temporada regular", "Playoffs", "Ambos"],
    horizontal=True
)
st.sidebar.markdown("---")


df_sel = df[df["season"] == int(selected_year)]
if game_type != "Ambos":
    df_sel = df_sel[df_sel["type"] == game_type]
df_sel = df_sel[df_sel["team"] == selected_team].copy()

if "seasongame" in df_sel.columns and df_sel["seasongame"].notna().any():
    df_sel = df_sel.sort_values(["game_date"])
else:
    df_sel = df_sel.sort_values(["game_date"])

st.title(f"{selected_team} — Temporada {selected_year}")

if df_sel.empty:
    st.warning("No hay datos para los filtros seleccionados.")
else:
    
    df_sel["is_win"] = (df_sel["game_result"] == "W").astype(int)
    df_sel["is_loss"] = (df_sel["game_result"] == "L").astype(int)
    df_sel["Acum Ganados"] = df_sel["is_win"].cumsum()
    df_sel["Acum Perdidos"] = df_sel["is_loss"].cumsum()

    
    fig_line = px.line(
        df_sel,
        x="game_date",
        y=["Acum Ganados", "Acum Perdidos"],
        labels={"value": "Acumulado", "variable": "Tipo", "game_date": "Fecha"},
        title=f"Acumulado de juegos ganados y perdidos — {selected_team} ({selected_year})",
        color_discrete_sequence=["#1f77b4", "#4a90e2"],  # tonos de azul
        template="plotly_white"
    )

    
    total_wins = int(df_sel["is_win"].sum())
    total_losses = int(df_sel["is_loss"].sum())
    fig_pie = px.pie(
        names=["Ganados", "Perdidos"],
        values=[total_wins, total_losses],
        title="Porcentaje de juegos ganados vs perdidos",
        hole=0.35,
        color_discrete_sequence=["#1f77b4", "#4a90e2"]
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_line, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pie, use_container_width=True)

    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Juegos totales", total_wins + total_losses)
        st.metric("Victorias", total_wins)
    with col2:
        st.metric("Derrotas", total_losses)
        if total_wins + total_losses > 0:
            st.metric("Win %", f"{total_wins / (total_wins + total_losses) * 100:.2f}%")

    
    st.markdown("### Últimos juegos")
    st.dataframe(
        df_sel[["season", "seasongame", "game_date", "team", "game_result", "type", "pts", "opp_id", "opp_pts"]]
        .sort_values(by=["game_date"], ascending=False)
        .head(50),
        use_container_width=True
