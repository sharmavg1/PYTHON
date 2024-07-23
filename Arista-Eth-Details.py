import pyeapi
import csv
from jinja2 import Template

def get_eos_version(ip_address, username, password):
    try:
        # Connect to the Arista switch
        connection = pyeapi.client.connect(
            transport='http',
            host=ip_address,
            username=username,
            password=password,
            timeout=5
        )
        node = pyeapi.client.Node(connection)
        
        # Execute the command to get EOS version
        result = node.enable("show version")
        eos_version = result[0]['result']['version']
        model = result[0]['result']['modelName']
        
        return model, eos_version
    except Exception as e:
        print(f"Error connecting to {ip_address}: {e}")
        return "Error retrieving model", "Error retrieving version"

def read_switch_details(csv_file_path):
    switches = []
    try:
        with open(csv_file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                switches.append({
                    "ip": row.get("IP"),
                    "username": row.get("Username"),
                    "password": row.get("Password"),
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        raise
    return switches

def generate_html_report(results, output_file_path):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Switch Report</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Switch Report</h1>
        <table>
            <tr>
                <th>IP Address</th>
                <th>Model</th>
                <th>EOS Version</th>
            </tr>
            {% for result in results %}
            <tr>
                <td>{{ result.ip }}</td>
                <td>{{ result.model }}</td>
                <td>{{ result.version }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    template = Template(html_template)
    html_content = template.render(results=results)

    with open(output_file_path, 'w') as file:
        file.write(html_content)

# Main
csv_file_path = 'switch_details.csv'  # Path to your CSV file
output_html_path = 'switch_report.html'  # Path where you want to save the HTML report

switches = read_switch_details(csv_file_path)
results = []

for switch in switches:
    ip = switch["ip"]
    username = switch["username"]
    password = switch["password"]

    model, version = get_eos_version(ip, username, password)
    results.append({
        "ip": ip,
        "model": model if model else "Not Accessible",
        "version": version if version else "Not Accessible"
    })

generate_html_report(results, output_html_path)
print(f"HTML report generated: {output_html_path}")
