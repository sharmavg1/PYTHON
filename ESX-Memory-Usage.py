import atexit
import ssl
import pandas as pd
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from jinja2 import Template

def get_host_ram_usage(content):
    memory_data = []
    for datacenter in content.rootFolder.childEntity:
        if isinstance(datacenter, vim.Datacenter):
            hostFolder = datacenter.hostFolder
            computeResourceList = hostFolder.childEntity
            for computeResource in computeResourceList:
                if isinstance(computeResource, vim.ClusterComputeResource) or isinstance(computeResource, vim.ComputeResource):
                    hostList = computeResource.host
                    for host in hostList:
                        total_memory = host.hardware.memorySize // (1024 * 1024 * 1024)  # Convert bytes to GB
                        used_memory = host.summary.quickStats.overallMemoryUsage // 1024  # Convert MB to GB
                        free_memory = total_memory - used_memory
                        ip_address = host.summary.managementServerIp

                        # Retrieve the IP address of the ESXi host
                        for nic in host.config.network.vnic:
                            ip_address = nic.spec.ip.ipAddress

                        memory_data.append({
                            'IP': ip_address,
                            'Total_Memory': total_memory,
                            'Used_Memory': used_memory,
                            'Free_Memory': free_memory
                        })
    return memory_data

def generate_html_report(data, output_file):
    template = Template('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESXi Memory Usage Report</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2>ESXi Memory Usage Report</h2>
        <table>
            <tr>
                <th>IP</th>
                <th>Total Memory (GB)</th>
                <th>Used Memory (GB)</th>
                <th>Free Memory (GB)</th>
            </tr>
            {% for entry in data %}
            <tr>
                <td>{{ entry.IP }}</td>
                <td>{{ entry.Total_Memory }}</td>
                <td>{{ entry.Used_Memory }}</td>
                <td>{{ entry.Free_Memory }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    ''')

    with open(output_file, 'w') as f:
        f.write(template.render(data=data))

def main():
    input_csv = 'esxi_details.csv'
    output_html = 'esxi_memory_usage_report.html'

    esxi_details = pd.read_csv(input_csv)
    memory_data = []

    # Disable SSL certificate verification
    context = ssl._create_unverified_context()

    for index, row in esxi_details.iterrows():
        try:
            si = SmartConnect(
                host=row['IP'],
                user=row['Username'],
                pwd=row['Password'],
                sslContext=context
            )
            atexit.register(Disconnect, si)

            content = si.RetrieveContent()
            memory_data.extend(get_host_ram_usage(content))

        except Exception as e:
            print(f"Failed to connect to ESXi server {row['IP']}: {str(e)}")

    generate_html_report(memory_data, output_html)
    print(f"HTML report generated: {output_html}")

if __name__ == "__main__":
    main()
