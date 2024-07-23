import csv
import paramiko
import re

def get_switch_info(ip_address, username, password):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip_address, username=username, password=password, timeout=5)

        # Get the FOS version
        stdin, stdout, stderr = ssh_client.exec_command("version")
        version_output = stdout.read().decode().strip()
        fos_version = None
        for line in version_output.splitlines():
            fos_match = re.search(r'Fabric OS:\s*(v[\d\.a-zA-Z]+)', line)
            if fos_match:
                fos_version = fos_match.group(1)
                break

        # Get the switch name and switch type
        stdin, stdout, stderr = ssh_client.exec_command("switchshow")
        switchshow_output = stdout.read().decode().strip()
        switch_name = None
        switch_type = None
        for line in switchshow_output.splitlines():
            name_match = re.search(r'switchName:\s*(.*)', line)
            type_match = re.search(r'switchType:\s*(.*)', line)
            if name_match:
                switch_name = name_match.group(1)
            if type_match:
                switch_type = type_match.group(1)

        ssh_client.close()
        return switch_name, switch_type, fos_version
    except Exception as e:
        print(f"Error connecting to {ip_address}: {e}")
        return "Error retrieving name", "Error retrieving type", "Error retrieving version"

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
                <th>Switch Name</th>
                <th>Switch Type</th>
                <th>FOS Version</th>
            </tr>
            {% for result in results %}
            <tr>
                <td>{{ result.ip }}</td>
                <td>{{ result.name }}</td>
                <td>{{ result.type }}</td>
                <td>{{ result.version }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    from jinja2 import Template
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

    name, switch_type, version = get_switch_info(ip, username, password)
    results.append({
        "ip": ip,
        "name": name if name else "Not Accessible",
        "type": switch_type if switch_type else "Not Accessible",
        "version": version if version else "Not Accessible"
    })

generate_html_report(results, output_html_path)
print(f"HTML report generated: {output_html_path}")
