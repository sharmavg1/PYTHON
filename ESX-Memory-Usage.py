import atexit
import ssl
import csv
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from jinja2 import Template

def read_esxi_servers_from_csv(csv_file_path):
    servers = []
    try:
        with open(csv_file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                servers.append({
                    "host": row["Host"],
                    "user": row["Username"],
                    "pwd": row["Password"],
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        raise
    return servers

def get_esxi_ip_address(host):
    # Retrieve IP address from the host's network configuration
    ip_address = None
    for network in host.config.network.vnic:
        if network.spec.ip.ipAddress:
            ip_address = network.spec.ip.ipAddress
            break
    return ip_address if ip_address else "N/A"

def get_host_info(content):
    results = []
    for datacenter in content.rootFolder.childEntity:
        if isinstance(datacenter, vim.Datacenter):
            hostFolder = datacenter.hostFolder
            computeResourceList = hostFolder.childEntity
            for computeResource in computeResourceList:
                if isinstance(computeResource, vim.ClusterComputeResource) or isinstance(computeResource, vim.ComputeResource):
                    hostList = computeResource.host
                    for host in hostList:
                        # Retrieve ESXi IP address
                        ip_address = get_esxi_ip_address(host)

                        total_memory_gb = host.hardware.memorySize / (1024 * 1024 * 1024)  # Convert bytes to GB
                        used_memory_gb = host.summary.quickStats.overallMemoryUsage / 1024  # MB to GB
                        free_memory_gb = total_memory_gb - used_memory_gb

                        # Retrieve ESXi version and build
                        esxi_version = host.summary.config.product.version
                        esxi_build = host.summary.config.product.build

                        results.append({
                            "ip": ip_address,
                            "total_memory_gb": total_memory_gb,
                            "used_memory_gb": used_memory_gb,
                            "free_memory_gb": free_memory_gb,
                            "version": esxi_version,
                            "build": esxi_build
                        })
    return results

def generate_html_report(results, output_file_path):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESXi Host Report</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>ESXi Host Report</h1>
        <table>
            <tr>
                <th>ESXi IP Address</th>
                <th>Total Memory (GB)</th>
                <th>Used Memory (GB)</th>
                <th>Free Memory (GB)</th>
                <th>ESXi Version</th>
                <th>Build Number</th>
            </tr>
            {% for result in results %}
            <tr>
                <td>{{ result.ip }}</td>
                <td>{{ result.total_memory_gb | round(2) }}</td>
                <td>{{ result.used_memory_gb | round(2) }}</td>
                <td>{{ result.free_memory_gb | round(2) }}</td>
                <td>{{ result.version }}</td>
                <td>{{ result.build }}</td>
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

def main():
    # Path to the CSV file containing ESXi server details
    csv_file_path = 'esxi_servers.csv'  # Update this path as necessary
    output_html_path = 'esxi_report.html'  # Path where you want to save the HTML report

    # Disable SSL certificate verification
    context = ssl._create_unverified_context()

    # Read server details from CSV
    esxi_servers = read_esxi_servers_from_csv(csv_file_path)
    all_results = []

    for esxi in esxi_servers:
        try:
            si = SmartConnect(
                host=esxi["host"],
                user=esxi["user"],
                pwd=esxi["pwd"],
                sslContext=context
            )
            atexit.register(Disconnect, si)

            content = si.RetrieveContent()
            results = get_host_info(content)
            all_results.extend(results)

        except Exception as e:
            print(f"Failed to connect to ESXi server {esxi['host']}: {str(e)}")

    # Generate HTML report
    generate_html_report(all_results, output_html_path)
    print(f"HTML report generated: {output_html_path}")

if __name__ == "__main__":
    main()
