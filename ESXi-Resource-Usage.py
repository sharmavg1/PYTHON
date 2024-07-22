import atexit
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# List of ESXi servers and credentials
esxi_servers = [
    {"host": "172.25.66.233", "user": "root", "pwd": 'Passw0rd!'},
    {"host": "172.25.66.231", "user": "root", "pwd": 'Passw0rd!'},
    {"host": "172.25.93.201", "user": "root", "pwd": 'Passw0rd!'},
]

def get_host_ram_usage(content):
    for datacenter in content.rootFolder.childEntity:
        if isinstance(datacenter, vim.Datacenter):
            hostFolder = datacenter.hostFolder
            computeResourceList = hostFolder.childEntity
            for computeResource in computeResourceList:
                if isinstance(computeResource, vim.ClusterComputeResource) or isinstance(computeResource, vim.ComputeResource):
                    hostList = computeResource.host
                    for host in hostList:
                        total_memory = host.hardware.memorySize // (1024 * 1024)  # Convert bytes to MB
                        used_memory = host.summary.quickStats.overallMemoryUsage  # MB
                        free_memory = total_memory - used_memory

                        print(f"ESXi Server: {host.name}")
                        print(f"Total Memory: {total_memory} MB")
                        print(f"Used Memory: {used_memory} MB")
                        print(f"Free Memory: {free_memory} MB")
                        print("--------------------------------------------")

def main():
    # Disable SSL certificate verification
    context = ssl._create_unverified_context()

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
            get_host_ram_usage(content)

        except Exception as e:
            print(f"Failed to connect to ESXi server {esxi['host']}: {str(e)}")

if __name__ == "__main__":
    main()
