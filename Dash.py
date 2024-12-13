# Install required packages - pip install dash pandas plotly networkx dash-bootstrap-components

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import networkx as nx
from datetime import datetime

# Example DataFrame
data = {
    "MMSI": ["211331640", "636091308", "311000072"],
    "Vessel Name": ["Sea Queen", "Ocean Explorer", "Atlantic Star"],
    "Type": ["Cargo", "Tanker", "Fishing"],
    "Flag": ["Germany", "Liberia", "Bahamas"],
    "Latitude": [53.5486, 29.9511, 34.0522],
    "Longitude": [9.9822, -90.0715, -118.2437],
    "Timestamp": [
        "2024-12-12 10:00:00",
        "2024-12-11 09:30:00",
        "2024-12-13 14:20:00"
    ],
    "Speed": [12.5, 15.2, 8.7],
    "Image URL": [
        "https://via.placeholder.com/300x200.png?text=Sea+Queen",
        "https://via.placeholder.com/300x200.png?text=Ocean+Explorer",
        "https://via.placeholder.com/300x200.png?text=Atlantic+Star"
    ]
}
df = pd.DataFrame(data)
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Example adjacency matrix for SNA (linkages at sea)
adj_matrix = pd.DataFrame(
    [[0, 1, 0],
     [1, 0, 1],
     [0, 1, 0]],
    index=["Sea Queen", "Ocean Explorer", "Atlantic Star"],
    columns=["Sea Queen", "Ocean Explorer", "Atlantic Star"]
)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Maritime Data Command Center"),
            dbc.Input(id="search-input", placeholder="Search MMSI or Vessel Name", type="text"),
            html.Br(),
            dcc.Dropdown(
                id="type-filter",
                options=[{"label": t, "value": t} for t in df["Type"].unique()],
                multi=True,
                placeholder="Filter by Vessel Type"
            ),
            dcc.Dropdown(
                id="flag-filter",
                options=[{"label": f, "value": f} for f in df["Flag"].unique()],
                multi=True,
                placeholder="Filter by Flag"
            ),
            dcc.DatePickerRange(
                id="date-filter",
                start_date=df["Timestamp"].min().date(),
                end_date=df["Timestamp"].max().date()
            ),
        ], width=3),
        dbc.Col([
            html.H2("Analytics Hub"),
            dcc.Tabs(id="analytics-tabs", value="map-tab", children=[
                dcc.Tab(label="Geospatial Analysis", value="map-tab"),
                dcc.Tab(label="Social Network Analysis", value="network-tab"),
                dcc.Tab(label="Vessel Images", value="images-tab")
            ]),
            html.Div(id="analytics-content"),
        ], width=9)
    ]),
    dbc.Row([
        dbc.Col([
            html.H2("Filtered Database"),
            dash_table.DataTable(
                id="database-table",
                columns=[{"name": col, "id": col} for col in df.columns],
                data=df.to_dict("records"),
                page_size=5,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left"},
                style_header={"fontWeight": "bold"}
            ),
            html.Br(),
            html.Button("Download CSV", id="download-btn", n_clicks=0, className="btn btn-primary"),
            dcc.Download(id="download-dataframe-csv")
        ], width=12)
    ])
])

# Callbacks
@app.callback(
    [Output("analytics-content", "children"),
     Output("database-table", "data")],
    [Input("analytics-tabs", "value"),
     Input("search-input", "value"),
     Input("type-filter", "value"),
     Input("flag-filter", "value"),
     Input("date-filter", "start_date"),
     Input("date-filter", "end_date")]
)
def update_analytics_and_table(tab, search, types, flags, start_date, end_date):
    # Filter Data
    filtered = df.copy()
    if search:
        filtered = filtered[filtered["MMSI"].str.contains(search) | filtered["Vessel Name"].str.contains(search, case=False)]
    if types:
        filtered = filtered[filtered["Type"].isin(types)]
    if flags:
        filtered = filtered[filtered["Flag"].isin(flags)]
    if start_date and end_date:
        filtered = filtered[(filtered["Timestamp"] >= pd.Timestamp(start_date)) & (filtered["Timestamp"] <= pd.Timestamp(end_date))]
    
    analytics_content = html.P("Select a tab to view content.")
    
    if tab == "map-tab":
        fig = px.scatter_geo(
            filtered, 
            lat="Latitude", 
            lon="Longitude", 
            hover_name="Vessel Name",
            title="Vessel Locations", 
            color="Type", 
            size="Speed"
        )
        fig.update_layout(
            geo=dict(
                showland=True,
                landcolor="rgb(243, 243, 243)",
                subunitcolor="rgb(217, 217, 217)",
                showocean=True,
                oceancolor="rgb(204, 230, 255)"
            ),
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            dragmode="zoom"
        )
        analytics_content = dcc.Graph(figure=fig)
    
    elif tab == "network-tab":
        G = nx.Graph()
        for row in adj_matrix.index:
            for col in adj_matrix.columns:
                if adj_matrix.loc[row, col] == 1:
                    G.add_edge(row, col)
        
        pos = nx.spring_layout(G)
        fig = px.scatter(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            text=list(G.nodes()),
            title="Social Network of Vessels"
        )
        analytics_content = html.Div([
            html.H4("Adjacency Matrix"),
            html.Pre(adj_matrix.to_string()),
            dcc.Graph(figure=fig)
        ])
    
    elif tab == "images-tab":
        images = [
            html.Div([
                html.Img(src=row["Image URL"], style={"width": "100%"}),
                html.P(row["Vessel Name"])
            ]) for _, row in filtered.iterrows() if row["Image URL"]
        ]
        analytics_content = html.Div(images, style={"display": "grid", "grid-template-columns": "repeat(auto-fill, minmax(300px, 1fr))", "gap": "10px"})
    
    return analytics_content, filtered.to_dict("records")

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-btn", "n_clicks"),
     Input("database-table", "data")]
)
def export_table_to_csv(n_clicks, table_data):
    if n_clicks > 0:
        filtered_df = pd.DataFrame(table_data)
        return dcc.send_data_frame(filtered_df.to_csv, "filtered_data.csv")

# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
