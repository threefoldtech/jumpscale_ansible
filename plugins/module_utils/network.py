from time import time

def add_node_to_network(network, zos, pool, node):
    node_ip_range = network.get_free_range()
    zos.network.add_node(network, node, node_ip_range, pool)

def update_network(zos, network):
    wids = []
    for network_resource in network.network_resources:
        wids.append(zos.workloads.deploy(network_resource))
    for wid in wids:
        wait_until_deployed(zos, wid)


def wait_until_deployed(zos, wid, expiration=3):
    start = time()

    while time() - start < expiration * 60:
        workload = zos.workloads.get(wid)
        if workload.info.result.workload_id:
            success = workload.info.result.state.value == 1
            if success:
                return True
            else:
                error_message = workload.info.result.message
                raise Exception(f"Failed to add node with workload id {wid} to the network due to the error: {error_message}")    
    raise TimeoutError(f"Failed to add the node to the network in time. Workload id is {wid}")

def is_node_in_network(network, node_id):
    return network.get_node_range(node_id) is not None
