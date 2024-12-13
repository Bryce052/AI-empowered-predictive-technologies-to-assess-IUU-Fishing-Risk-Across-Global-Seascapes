import dash
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import networkx as nx
from datetime import datetime

# Example DataFrame with potential missing values fixed for the 3rd record
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Layout
app.layout = dbc.Container([
    # Header Row
    dbc.Row([
        dbc.Col(html.H2("Maritime Data Command Center", className="text-center text-primary font-weight-bold"), width=12)
    ], className="mb-4"),

    # Main Dashboard Layout with Sidebar and Content
    dbc.Row([
        # Sidebar for Filters
        dbc.Col([
            html.Div([
                html.H4("Filters", className="text-info"),
                dbc.Input(id="search-input", placeholder="Search MMSI or Vessel Name", type="text", className="mb-3"),
                
                # Vessel Type Filter
                dbc.Row([
                    dbc.Col(dbc.Label("Vessel Type", html_for="type-filter"), width=12),
                    dbc.Col(dcc.Dropdown(
                        id="type-filter",
                        options=[{"label": t, "value": t} for t in df["Type"].unique()],
                        multi=True,
                        placeholder="Select Vessel Type",
                        className="mb-3"
                    ), width=12)
                ], className="mb-3"),
                
                # Flag Filter
                dbc.Row([
                    dbc.Col(dbc.Label("Flag", html_for="flag-filter"), width=12),
                    dbc.Col(dcc.Dropdown(
                        id="flag-filter",
                        options=[{"label": f, "value": f} for f in df["Flag"].unique()],
                        multi=True,
                        placeholder="Select Flag",
                        className="mb-3"
                    ), width=12)
                ], className="mb-3"),
                
                # Date Filter
                dbc.Row([
                    dbc.Col(dbc.Label("Date Range", html_for="date-filter"), width=12),
                    dbc.Col(dcc.DatePickerRange(
                        id="date-filter",
                        start_date=df["Timestamp"].min().date(),
                        end_date=df["Timestamp"].max().date(),
                        display_format="YYYY-MM-DD",
                        className="mb-3"
                    ), width=12)
                ], className="mb-3"),
            ], className="border p-4 bg-light rounded"),

        ], width=3),

        # Main Content Area for Analytics
        dbc.Col([
            html.Div([
                dcc.Tabs(id="analytics-tabs", value="map-tab", children=[
                    dcc.Tab(label="Geospatial Analysis", value="map-tab", className="bg-info text-white"),
                    dcc.Tab(label="Social Network Analysis", value="network-tab", className="bg-info text-white"),
                    dcc.Tab(label="Vessel Images", value="images-tab", className="bg-info text-white"),
                ], className="mb-4"),
                html.Div(id="analytics-content"),
            ])
        ], width=9)
    ], className="mb-4"),

    # Data Table and Download Section
    dbc.Row([
        dbc.Col([
            html.H4("Filtered Database", className="text-info mb-3"),
            dash_table.DataTable(
                id="database-table",
                columns=[{"name": col, "id": col} for col in df.columns],
                data=df.to_dict("records"),
                page_size=5,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "fontSize": "14px", "padding": "10px"},
                style_header={"fontWeight": "bold", "backgroundColor": "lightblue"},
                style_data_conditional=[{
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgba(0, 116, 217, 0.05)"
                }],
                row_selectable="multi",  # Enable multiple row selection
                selected_rows=[],  # Initially no rows selected
            ),
            html.Br(),
            dbc.Button("Download CSV", id="download-btn", n_clicks=0, color="primary", className="mt-3"),
            dcc.Download(id="download-dataframe-csv"),
            html.Button("Download Map", id="download-map-btn", n_clicks=0, className="btn btn-primary mt-3")
        ])
    ])
], fluid=True)

# Callbacks
@app.callback(
    [Output("analytics-content", "children"),
     Output("database-table", "data")],
    [Input("analytics-tabs", "value"),
     Input("search-input", "value"),
     Input("type-filter", "value"),
     Input("flag-filter", "value"),
     Input("date-filter", "start_date"),
     Input("date-filter", "end_date"),
     Input("database-table", "selected_rows")]
)
def update_analytics_and_table(tab, search, types, flags, start_date, end_date, selected_rows):
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

    # Handle selected rows for visuals (only update visual content)
    selected_vessels = []
    if selected_rows:
        try:
            selected_vessels = [filtered.iloc[row]["Vessel Name"] for row in selected_rows]
            filtered = filtered[filtered["Vessel Name"].isin(selected_vessels)]
        except IndexError:
            filtered = pd.DataFrame()  # Ensure it doesn't break the code if the index is out of bounds

    # Prepare Analytics Content
    analytics_content = html.P("Select a tab to view content.")
    
    if tab == "map-tab":
        if not filtered.empty:
            fig = px.scatter_geo(
                filtered, 
                lat="Latitude", 
                lon="Longitude", 
                hover_name="Vessel Name",
                title="Vessel Locations", 
                color="Type", 
                size="Speed",
                size_max=10  # Reducing size of points on the map
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
        else:
            analytics_content = html.P("No vessels matching the filters.")

    elif tab == "network-tab":
        if not filtered.empty:
            G = nx.Graph()
            for row in adj_matrix.index:
                for col in adj_matrix.columns:
                    if adj_matrix.loc[row, col] == 1:
                        G.add_edge(row, col)

            subgraph = G.subgraph(selected_vessels) if selected_vessels else G
            pos = nx.spring_layout(subgraph)
            fig = px.scatter(
                x=[pos[node][0] for node in subgraph.nodes()],
                y=[pos[node][1] for node in subgraph.nodes()],
                text=list(subgraph.nodes()),
                title="Social Network of Vessels"
            )
            analytics_content = html.Div([
                html.H4("Adjacency Matrix"),
                html.Pre(adj_matrix.to_string()),
                dcc.Graph(figure=fig)
            ])
        else:
            analytics_content = html.P("No vessels selected or matching filters.")

    elif tab == "images-tab":
        if not filtered.empty:
            images = [
                html.Div([
                    html.Img(src=row["Image URL"], style={"width": "100%", "border-radius": "8px"}),
                    html.P(row["Vessel Name"], className="text-center")
                ]) for _, row in filtered.iterrows() if row["Image URL"]
            ]
            analytics_content = html.Div(images, style={"display": "grid", "grid-template-columns": "repeat(auto-fill, minmax(300px, 1fr))"})
        else:
            analytics_content = html.P("No vessels matching the filters.")

    # Update table data
    return analytics_content, df.to_dict("records")

# Download CSV callback
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-btn", "n_clicks"),
    State("database-table", "data")
)
def download_csv(n_clicks, table_data):
    if n_clicks > 0:
        return dict(content=pd.DataFrame(table_data).to_csv(), filename="filtered_vessels.csv")

if __name__ == '__main__':
    app.run_server(debug=True)
