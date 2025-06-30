import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Main data files
DATA_FILE = "combined_hourly_energy.csv"
CLIMATE_FILE = "Climate zone.csv"

@st.cache_data
def load_data(data_file, climate_file):
    df = pd.read_csv(data_file)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    climate_df = pd.read_csv(climate_file)
    merged_df = df.merge(climate_df, how='left', left_on='Building', right_on='Building Name')

    if merged_df['Climate zone'].isnull().any():
        st.warning("Some buildings are missing climate zone data.")

    merged_df = merged_df.sort_values(by=['Building', 'Timestamp'])
    return merged_df

def main():
    st.title("🏢 At Home - Hourly Energy Analysis")

    try:
        df = load_data(DATA_FILE, CLIMATE_FILE)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    climate_df2 = pd.read_csv(CLIMATE_FILE)

    csv_all = df.to_csv(index=False).encode("utf-8")

    climate_zones = df['Climate zone'].dropna().unique()
    checkbox = st.button("List climate zones")
    if checkbox:
        st.write(climate_df2)
    selected_zones = st.multiselect("Select Climate Zones", sorted(climate_zones))

    filtered_df = df[df['Climate zone'].isin(selected_zones)] if selected_zones else df

    buildings = filtered_df['Building'].unique()
    selected_buildings = st.multiselect("Select Buildings", sorted(buildings))

    plot_df = filtered_df[filtered_df['Building'].isin(selected_buildings)] if selected_buildings else filtered_df
    # st.dataframe(plot_df)
    if plot_df.empty:
        st.warning("No data for the selected options.")
        return

    # Original Energy Use graph
    fig = go.Figure()
    for building in plot_df['Building'].unique():
        bldg_data = plot_df[plot_df['Building'] == building]
        fig.add_trace(go.Scatter(
            x=bldg_data['Timestamp'],
            y=bldg_data['CTR01_BuildingEnergy_kWhHourly(kW-hr)'],
            mode='lines',
            name=f"{building} (Energy)"
        ))

    fig.update_layout(
        title='Hourly Energy Use',
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
        yaxis_title="Energy (kWh)",
        xaxis_title="Timestamp",
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)


    # EUI Graph
    eui_fig = go.Figure()
    
    # Add EUI traces
    for building in plot_df['Building'].unique():
        bldg_data = plot_df[plot_df['Building'] == building]
        if 'Area' in bldg_data.columns and bldg_data['Area'].notnull().all():
            bldg_data = bldg_data.copy()
            bldg_data['EUI'] = bldg_data['CTR01_BuildingEnergy_kWhHourly(kW-hr)'] / bldg_data['Area']
            eui_fig.add_trace(go.Scatter(
                x=bldg_data['Timestamp'],
                y=bldg_data['EUI'],
                mode='lines',
                name=f"{building} (EUI)"
            ))
    
    # Shade 6AM to 9PM for each date
    for date in plot_df['Timestamp'].dt.normalize().unique():
        start = pd.Timestamp(date) + pd.Timedelta(hours=6)
        end = pd.Timestamp(date) + pd.Timedelta(hours=9, minutes=30)
        eui_fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor="LightBlue",
            opacity=0.2,
            layer="below",
            line_width=0,
        )
    
    # Layout updates
    eui_fig.update_layout(
        title='Hourly Energy Use Intensity (EUI)',
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
        yaxis_title="EUI (kWh/sqft)",
        xaxis_title="Timestamp",
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(eui_fig, use_container_width=True)

        

    if not plot_df.empty:
        # Pull summary stats from the climate_df2 (which has base/peak load data)
        climate_df2['Base to Peak Ratio'] = climate_df2['Base load'] / climate_df2['Peak load']
        stats_cols = ['Building Name', 'Peak load', 'Base load', 'Base to Peak Ratio', 'Area']

        summary_df = climate_df2[climate_df2['Building Name'].isin(plot_df['Building'].unique())][stats_cols]
        summary_df = summary_df.rename(columns={"Building Name": "Building"})

        st.subheader("📊 Building Summary Metrics")
        st.dataframe(summary_df.set_index('Building'))



        csv_filtered = plot_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Selected Data",
            data=csv_filtered,
            file_name="selected_buildings_energy.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
