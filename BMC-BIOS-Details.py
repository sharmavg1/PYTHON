import paramiko
import json
import csv
from datetime import datetime

def get_server_versions(UCPAdvisor_ip, UCPAdvisor_username, UCPAdvisor_password, bmc_ip, bmc_username, bmc_password):
    command = (
        f'curl -s -k '
        f'-H "X-Management-IPs: {bmc_ip}" '
        f'-H "X-Subsystem-User: {bmc_username}" '
        f'-H "X-Subsystem-Password: {bmc_password}" '
        f'https://{UCPAdvisor_ip}:8444/v9/compute/servers/1'
    )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(UCPAdvisor_ip, username=UCPAdvisor_username, password=UCPAdvisor_password)

    try:
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        output_json = json.loads(output)
        server_details = output_json.get("server", {})
        BIOS_Version = server_details.get("BIOSversion", "Unknown")
        BMC_Version = server_details.get("firmwareVersion", "Unknown")
        return BMC_Version, BIOS_Version
    finally:
        client.close()

def read_server_details(csv_file_path):
    servers = []
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            servers.append({
                "BMCip": row["BMCip"],
                "username": row["username"],
                "password": row["password"]
            })
    return servers

def generate_html_report(results, filename="report.html"):
    html_content = f"""
    <html>
    <head>
        <title>Server Versions Report</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table, th, td {{
                border: 1px solid black;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>Server Versions Report</h1>
        <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table>
            <tr>
                <th>BMC IP</th>
                <th>BMC Version</th>
                <th>BIOS Version</th>
            </tr>
    """

    for server in results:
        html_content += f"""
            <tr>
                <td>{server['BMCip']}</td>
                <td>{server['BMC_Version']}</td>
                <td>{server['BIOS_Version']}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(filename, "w") as file:
        file.write(html_content)

def main():
    csv_file_path = 'servers.csv'
    UCPAdvisor_ip = "172.25.93.250"
    UCPAdvisor_username = "ucpadmin"
    UCPAdvisor_password = "Advisor@22"

    servers = read_server_details(csv_file_path)
    results = []

    for server in servers:
        bmc_ip = server["BMCip"]
        bmc_username = server["username"]
        bmc_password = server["password"]

        BMC_Version, BIOS_Version = get_server_versions(UCPAdvisor_ip, UCPAdvisor_username, UCPAdvisor_password, bmc_ip, bmc_username, bmc_password)

        results.append({
            "BMCip": bmc_ip,
            "BMC_Version": BMC_Version,
            "BIOS_Version": BIOS_Version
        })

    generate_html_report(results)

if __name__ == "__main__":
    main()
