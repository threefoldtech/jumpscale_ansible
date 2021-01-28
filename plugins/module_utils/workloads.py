from time import time
from jumpscale.clients.explorer.models import NextAction

def decommission_workloads(zos, wids):
    for wid in wids:
        zos.workloads.decomission(wid)
    for wid in wids:
        wait_until_decommissioned(zos, wid)

def wait_until_decommissioned(zos, wid, expiration=3):
    start = time()

    while time() - start < expiration * 60:
        workload = zos.workloads.get(wid)
        if workload.info.next_action == NextAction.DELETED or workload.info.next_action == NextAction.DELETE:
            return True
            
    raise TimeoutError(f"Failed to decmmission wid {wid}")

