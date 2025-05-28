import pandas as pd
import streamlit as st
import plotly.graph_objects as go

DATA_FILE = "combined_hourly_energy.csv"

@st.cache_data
def load_combined_data(file_path):
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values(by=['Building', 'Timestamp'])
    return df

def main():
    st.title("🏢 At Home - Hourly Energy Analysis")

    try:
        df = load_combined_data(DATA_FILE)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    st.dataframe(df.head())

    csv_all = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download All Data", data=csv_all, file_name="all_buildings_energy.csv", mime="text/csv")

    buildings = df['Building'].unique()
    selected_building = st.selectbox("Select Building", buildings)

    building_df = df[df['Building'] == selected_building]

    if building_df.empty:
        st.warning("No data for the selected building.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=building_df['Timestamp'],
        y=building_df['CTR01_BuildingEnergy_kWhHourly(kW-hr)'],
        mode='lines',
        name='Energy (kWh)'
    ))

    fig.update_layout(
        title=f'Hourly Energy Use – {selected_building}',
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(step="all", label="All")
                ]
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis_title="CTR01_BuildingEnergy_kWhHourly(kW-hr)",
        xaxis_title="Timestamp",
        template="plotly_white",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    csv_building = building_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {selected_building} Data",
        data=csv_building,
        file_name=f"{selected_building}_energy.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
