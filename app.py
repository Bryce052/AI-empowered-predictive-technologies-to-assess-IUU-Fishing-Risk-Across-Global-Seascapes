from flask import Flask, request, jsonify, render_template, url_for, send_file, make_response
import sqlite3
import pandas as pd
import folium
import os
import re
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"


# Database connection function
def connect_to_database(db_name="maritime_data.db"):
    return sqlite3.connect(db_name)


# Function to clean user input
def clean_input(text):
    """Removes punctuation and extra spaces from user input."""
    return re.sub(r"[^\w\s]", "", text).strip()


# Function to extract speed range from the query
def extract_speed_range(user_query):
    """Extracts the speed range (min and max) from a query if present."""
    speeds = [float(s) for s in user_query.split() if s.replace('.', '', 1).isdigit()]
    if len(speeds) == 2:
        return speeds[0], speeds[1]
    return None, None


# Function to extract flag name from the query
def extract_flag(user_query):
    """Extracts the flag from a flag-related query."""
    flag_query = user_query.split("flag")[-1].strip()
    flag_query = re.sub(r"the|under|registered", "", flag_query).strip()
    return flag_query


# Function to extract vessel name intelligently
def extract_vessel_name(user_query):
    """Tries to extract the vessel name from the user's query."""
    phrases = ["named", "called", "find vessel", "search for", "tell me about", "look for", "find"]
    for phrase in phrases:
        if phrase in user_query:
            # Extract everything after the phrase
            vessel_name = user_query.split(phrase, 1)[1].strip()
            return vessel_name
    return None


# Function to export data to CSV
def export_data_to_csv(query):
    conn = connect_to_database()
    data = pd.read_sql_query(query, conn)
    conn.close()

    # Create CSV content in memory
    output = io.StringIO()
    data.to_csv(output, index=False)
    output.seek(0)
    return output


# Function to generate geospatial maps
def generate_map(data):
    """Generate an interactive map from vessel data."""
    m = folium.Map(location=[0, 0], zoom_start=2)
    for _, row in data.iterrows():
        lat, lon = eval(row['last_known_position'])  # Parse string to tuple
        folium.Marker([lat, lon], popup=row['vessel_name']).add_to(m)
    return m


# Function to generate a social network diagram
def generate_network_diagram(data):
    """Create a social network diagram of vessels, owners, and visited ports."""
    import networkx as nx

    G = nx.Graph()

    for _, row in data.iterrows():
        vessel = row['vessel_name']
        owner = row['owner']
        ports = eval(row['visited_ports'])  # Parse string to list
        G.add_node(vessel, type='vessel')
        G.add_node(owner, type='owner')
        G.add_edge(vessel, owner)

        for port in ports:
            G.add_node(port, type='port')
            G.add_edge(vessel, port)

    # Generate the diagram
    plt.figure(figsize=(10, 10))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue', font_size=10)
    plt.title("Social Network Diagram")
    output = io.BytesIO()
    plt.savefig(output, format='png')
    output.seek(0)
    return output


# Main query processing function
def process_query(user_query):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Clean and normalize the user query
        user_query = clean_input(user_query.lower())

        # Handle Speed-Based Queries
        if "speed" in user_query or "knots" in user_query:
            min_speed, max_speed = extract_speed_range(user_query)
            if min_speed is not None and max_speed is not None:
                cursor.execute(
                    "SELECT vessel_name, speed_knots FROM vessels WHERE speed_knots BETWEEN ? AND ?",
                    (min_speed, max_speed)
                )
                results = cursor.fetchall()
                conn.close()
                if results:
                    return {"response": "I found these vessels within your speed range:\n" +
                                        "\n".join([f"{name} ({speed} knots)" for name, speed in results])}
                return {"response": "I couldn’t find any vessels within that speed range."}
            return {"response": "It looks like there's an issue with the speed format. Try something like: 'speed 10 to 20'."}

        # Handle Owner-Based Queries
        if "owned by" in user_query:
            owner = user_query.split("owned by")[-1].strip()
            cursor.execute("SELECT vessel_name FROM vessels WHERE LOWER(owner) = ?", (owner.lower(),))
            results = cursor.fetchall()
            conn.close()
            if results:
                return {"response": f"The following vessels are owned by {owner.capitalize()}:\n" +
                                    ", ".join([row[0] for row in results])}
            return {"response": f"I couldn’t find any vessels owned by {owner.capitalize()}."}

        # Handle Vessel Name Queries
        if "vessel" in user_query:
            vessel_name = extract_vessel_name(user_query)
            if vessel_name:
                cursor.execute(
                    '''SELECT vessel_name, vessel_type, owner, flag, speed_knots, dimensions,
                              visited_ports, last_known_position, status, mmsi
                       FROM vessels
                       WHERE LOWER(vessel_name) = ?''',
                    (vessel_name.lower(),)
                )
                result = cursor.fetchone()
                conn.close()
                if result:
                    (
                        vessel_name,
                        vessel_type,
                        owner,
                        flag,
                        speed_knots,
                        dimensions,
                        visited_ports,
                        last_known_position,
                        status,
                        mmsi,
                    ) = result
                    return {"response": (
                        f"The {vessel_name} is a {vessel_type} vessel owned by {owner}. "
                        f"It sails under the {flag} flag and can travel at a maximum speed of {speed_knots} knots. "
                        f"Recently, it was near {last_known_position} and its current status is '{status}'. "
                        f"It has visited ports such as {visited_ports}."
                    )}
                return {"response": f"I couldn’t find any vessel named '{vessel_name}'."}

        # Handle Status Queries
        if any(status in user_query for status in ["in transit", "docked", "active"]):
            if "in transit" in user_query:
                status = "in transit"
            elif "docked" in user_query:
                status = "docked"
            elif "active" in user_query:
                status = "active"

            cursor.execute("SELECT vessel_name FROM vessels WHERE LOWER(status) = ?", (status,))
            results = cursor.fetchall()
            conn.close()
            if results:
                return {"response": f"The following vessels are currently '{status.capitalize()}':\n" +
                                    ", ".join([row[0] for row in results])}
            return {"response": f"I couldn’t find any vessels with the status '{status.capitalize()}'."}

        # Handle Flag Queries
        if "flag" in user_query or "registered under" in user_query or "sail under" in user_query:
            flag = extract_flag(user_query)
            cursor.execute("SELECT vessel_name FROM vessels WHERE LOWER(flag) LIKE ?", (f"%{flag.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            if results:
                return {"response": f"Under the {flag.capitalize()} flag, I found the following vessels: " +
                                    ", ".join([row[0] for row in results])}
            return {"response": f"I couldn’t find any vessels registered under the {flag.capitalize()} flag."}

        # Handle CSV Export
        if "export" in user_query or "csv" in user_query:
            query = "SELECT * FROM vessels WHERE status = 'In Transit'"
            csv_content = export_data_to_csv(query)
            response = make_response(csv_content.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=vessels_in_transit.csv"
            response.headers["Content-Type"] = "text/csv"
            return response

        return {"response": "I'm sorry, I didn’t quite understand your request. Can you try rephrasing it?"}

    except Exception as e:
        return {"response": f"An error occurred: {e}"}
    finally:
        conn.close()
# Function to export data to CSV
def export_data_to_csv(query):
    conn = connect_to_database()
    data = pd.read_sql_query(query, conn)
    conn.close()

    # Generate CSV content in memory
    output = io.StringIO()
    data.to_csv(output, index=False)
    output.seek(0)
    return output

@app.route("/process", methods=["POST"])
def process_chat():
    user_query = request.json.get("query", "")

    # Check for export requests
    if "export" in user_query.lower() or "csv" in user_query.lower():
        query = "SELECT * FROM vessels WHERE status = 'In Transit'"
        csv_content = export_data_to_csv(query)
        response = make_response(csv_content.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=vessels_in_transit.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    response = process_query(user_query)
    return jsonify({"response": response["response"]})


@app.route("/")
def chatbot():
    return render_template("chat.html")


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
