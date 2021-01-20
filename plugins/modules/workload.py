#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j
from jumpscale.clients.explorer.models import NextAction, WorkloadType



DOCUMENTATION = r'''
---
module: workload

short_description: workload module for zos

version_added: "1.0.0"

description: module to get workload(s) facts and manage their state on the TFGrid.

options:
    identity_name:
        description: identity name to be used to deploy the container defaults to j.core.identity.me
        required: False
        type: str
    wid:
        description: id for the workload to fetch/change it's state
        required: False
        type: int
    next_action:
        description: filters the listed workload by their next action
        required: False
        type: str
    owner_tid:
        description: owner id to use in listing workloads
        required: False
        type: int
    state:
        description: state of the workload. used to decomission/deploy a workload if it doesn't match the specified state
        required: False
        type: str
        choices: [present, deleted]
    types:
        description: filters the listed workloads by the types specified
        required: False
        type: list
    match: 
        description: key/value pairs to filter by
        required: False
        type: str
        choices: [present, deleted]

author:
    - Maged Motawea (@m-motawea)
    
'''



RETURN = r'''
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
message:
    description: The output message that the module generates.
    type: dict
    returned: always
    sample: "{'id': 1185, 'size': 15, 'network_id': 'k8s', 'ipaddress': '10.200.1.235', 'cluster_secret': 'dcf64382af2d86ea31b2712e406383732326e1d616f26bfd11bb3c4346476bfeff7a791ceec9dd3982f8d8dc9e53b93cd06e8624', 'master_ips': ['10.200.0.212'], 'ssh_keys': ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDjUg2WbMNHMAgaq1MWfNNJGUPdTxbeK/gLaC3kEMRbXlciiWvHa0az1VOHKFuj36KJcujJGuL2jDlkRPjxuaWhxzyDLYEIvMdAq15Ny8L0JIAGoiY0WKsoQEkxmPmV1j4ziuOga3MWdIkTcfkhrGbz3QzAy/awm4uSUWziXiVN/9jii/Ww2D/SzudgFnFlQn2kKMbqFboqecY+8r9gFl6sBWal9u6zrHwl3NeRZSo8IGhFXHM/fXT0dAKl+3J1CqJOcMkaTLjt36W88mtiPLV6VO4r9VSDCfWzOqfg9/r0kgbQEfQ0PWt36U7nt+qKZx6Iegr6tJ3EFMOmiK41OeXx maged@maged-Inspiron-3576'], 'public_ip': 0, 'stats_aggregator': [], 'info': {'workload_id': 1, 'node_id': '8zPYak76CXcoZxRoJBjdU69kVjo7XYU1SFE2NEK4UMqn', 'pool_id': 149, 'description': '', 'reference': '', 'customer_tid': 132, 'customer_signature': '8f70b338eda4f664671d3ba847c97a3778484c16a3479224ef02c2bf8764346672cd57df9bf212f69010dea8c9297810fa12c95b79201f5b51d78a7419aa8900', 'next_action': 6, 'signatures_provision': [], 'signing_request_provision': {'signers': [], 'quorum_min': 0}, 'signing_request_delete': {'signers': [132], 'quorum_min': 1}, 'signatures_farmer': [], 'signatures_delete': [{'tid': 132, 'signature': '3bad5239a74ab561bf2e12642dc78a3945433eb29296bf672d785a0f5e1aa8e100f0e34e46ac55da32e9aff2f4aeace49e68c596f31dc76d65ca0000f9b81401', 'epoch': 1610961740}], 'epoch': 1610961692, 'metadata': '', 'result': {'category': 4, 'workload_id': '1185-1', 'data_json': '{\"id\": \"1185-1\", \"ip\": \"10.200.1.235\"}', 'signature': 'bfb07a13a45fbc03e293a8443af450ab5854db3fd2252a0b30efca8daa217c72c1292762a21bf525e22066d7fef0fe711bf43537489e6e9258ff62878ac5e508', 'state': 2, 'message': '', 'epoch': 1610961706}, 'workload_type': 4}}"
ansible_facts:
    description: facts of the workloads as specified in module params.
    type: dict
    returned: always
    sample: "{'workloads': [{'id': 1185, 'size': 15, 'network_id': 'k8s', 'ipaddress': '10.200.1.235', 'cluster_secret': 'dcf64382af2d86ea31b2712e406383732326e1d616f26bfd11bb3c4346476bfeff7a791ceec9dd3982f8d8dc9e53b93cd06e8624', 'master_ips': ['10.200.0.212'], 'ssh_keys': ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDjUg2WbMNHMAgaq1MWfNNJGUPdTxbeK/gLaC3kEMRbXlciiWvHa0az1VOHKFuj36KJcujJGuL2jDlkRPjxuaWhxzyDLYEIvMdAq15Ny8L0JIAGoiY0WKsoQEkxmPmV1j4ziuOga3MWdIkTcfkhrGbz3QzAy/awm4uSUWziXiVN/9jii/Ww2D/SzudgFnFlQn2kKMbqFboqecY+8r9gFl6sBWal9u6zrHwl3NeRZSo8IGhFXHM/fXT0dAKl+3J1CqJOcMkaTLjt36W88mtiPLV6VO4r9VSDCfWzOqfg9/r0kgbQEfQ0PWt36U7nt+qKZx6Iegr6tJ3EFMOmiK41OeXx maged@maged-Inspiron-3576'], 'public_ip': 0, 'stats_aggregator': [], 'info': {'workload_id': 1, 'node_id': '8zPYak76CXcoZxRoJBjdU69kVjo7XYU1SFE2NEK4UMqn', 'pool_id': 149, 'description': '', 'reference': '', 'customer_tid': 132, 'customer_signature': '8f70b338eda4f664671d3ba847c97a3778484c16a3479224ef02c2bf8764346672cd57df9bf212f69010dea8c9297810fa12c95b79201f5b51d78a7419aa8900', 'next_action': 6, 'signatures_provision': [], 'signing_request_provision': {'signers': [], 'quorum_min': 0}, 'signing_request_delete': {'signers': [132], 'quorum_min': 1}, 'signatures_farmer': [], 'signatures_delete': [{'tid': 132, 'signature': '3bad5239a74ab561bf2e12642dc78a3945433eb29296bf672d785a0f5e1aa8e100f0e34e46ac55da32e9aff2f4aeace49e68c596f31dc76d65ca0000f9b81401', 'epoch': 1610961740}], 'epoch': 1610961692, 'metadata': '', 'result': {'category': 4, 'workload_id': '1185-1', 'data_json': '{\"id\": \"1185-1\", \"ip\": \"10.200.1.235\"}', 'signature': 'bfb07a13a45fbc03e293a8443af450ab5854db3fd2252a0b30efca8daa217c72c1292762a21bf525e22066d7fef0fe711bf43537489e6e9258ff62878ac5e508', 'state': 2, 'message': '', 'epoch': 1610961706}, 'workload_type': 4}}]}"
'''


def filter_workload(workload, filters):
    for key, val in filters.items():
        split_keys = key.split(".")
        attr = workload
        for key in split_keys:
            if not hasattr(attr, key):
                return False
            attr = getattr(attr, key)
        if attr != val:
            return False
    return True


def run_module():
    next_action_choices = [a.name.lower() for a in NextAction]
    type_choices = [t.name.lower() for t in WorkloadType]
    module_args = dict(
        identity_name=dict(type='str', required=False),
        wid=dict(type='int', required=False),
        next_action=dict(type='str', required=False, default=None, choices=next_action_choices),
        owner_tid=dict(type='int', required=False),
        state=dict(type='str', required=False, choices=["present", "deleted"]),
        types=dict(type='list', required=False, default=[], choices=type_choices),
        match=dict(type='dict', required=False, default={}),
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        types=type_choices,
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    identity = j.core.identity.find(module.params['identity_name']) if module.params['identity_name'] else j.core.identity.me
    zos = j.sals.zos.get(module.params['identity_name'])
    if not module.params["state"]:
        # gather facts
        if module.params["wid"]:
            w = zos.workloads.get(module.params["wid"])
            result["ansible_facts"] = {"workloads": [w.to_dict()]}
        else:
            workload_types = []
            if module.params["types"]:
                for workload_type in module.params["types"]:
                    workload_types.append(workload_type.lower())
                result["types"] = workload_types
            else:
                workload_types = type_choices
            owner_tid = module.params["owner_tid"] or identity.tid
            next_action = module.params["next_action"].upper() if module.params["next_action"] else None
            workloads = zos.workloads.list(owner_tid, next_action)
            filtered_workloads = []
            for workload in workloads:
                if not filter_workload(workload, module.params["match"]):
                    continue
                filtered_workloads.append(workload)
            filtered_workloads = [w for w in filtered_workloads if w.info.workload_type.name.lower() in workload_types]
            result["ansible_facts"] = {"workloads": [w.to_dict() for w in filtered_workloads]}
    else:
        # apply state
        w = zos.workloads.get(module.params["wid"])
        if module.params["state"] == "deleted":
            if w.info.next_action.value <= NextAction.DEPLOY.value:
                zos.workloads.decomission(w.id)
                result["changed"] = True
                w = zos.workloads.get(w.id)
        elif module.params["state"] == "present":
            if w.info.next_action.value > NextAction.DEPLOY.value:
                wid = zos.workloads.deploy(w)
                result["changed"] = True
                w = zos.workloads.get(wid)
        result["message"] = w.to_dict()

    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()