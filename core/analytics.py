import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def show_status_donut(df):
    """Donut chart showing proportion of Normal vs High vs Low parameters."""
    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {"Normal": "#059669", "High": "#DC2626", "Low": "#D97706", "Unknown": "#9CA3AF"}

    fig = px.pie(
        status_counts,
        names="Status",
        values="Count",
        hole=0.55,
        color="Status",
        color_discrete_map=color_map
    )
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(height=350, showlegend=True, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

def show_range_position_chart(df, parse_range_func):
    """
    Horizontal chart showing where each abnormal parameter's value falls
    relative to its normal range (0 = low bound, 1 = high bound).
    """
    rows = []
    for _, row in df.iterrows():
        if row["Status"] not in ["High", "Low"]:
            continue
        low, high = parse_range_func(row["Reference Range"])
        try:
            value = float(row["Result"])
        except ValueError:
            continue
        if low is None or high is None or high == low:
            continue

        position = (value - low) / (high - low)
        rows.append({
            "Parameter": row["Parameter"],
            "Position": position,
            "Status": row["Status"]
        })

    if not rows:
        st.info("No abnormal parameters to chart — all values are within range.")
        return

    color_map = {"High": "#DC2626", "Low": "#D97706"}

    fig = go.Figure()

    for r in rows:
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[r["Parameter"], r["Parameter"]],
            mode="lines",
            line=dict(color="#E2E8F0", width=6),
            showlegend=False,
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=[r["Position"]],
            y=[r["Parameter"]],
            mode="markers",
            marker=dict(size=14, color=color_map.get(r["Status"], "#6B7280")),
            name=r["Status"],
            showlegend=False,
            hovertemplate=f"{r['Parameter']}: {r['Status']}<extra></extra>"
        ))

    fig.update_layout(
        height=max(250, 60 * len(rows)),
        xaxis=dict(range=[-0.2, 1.2], showticklabels=False, title="Relative to normal range (low → high)"),
        margin=dict(t=20, b=40, l=20, r=20)
    )
    st.plotly_chart(fig, use_container_width=True)