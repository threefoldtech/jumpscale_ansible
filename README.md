# Ansible Collection - threefold.jsgrid

Ansible galaxy collection for the js-grid repo. It exposes the functionality of zos as ansible modules. Sample playbooks are present in the docs directory.

## Modules
Modules are present in `plugins/modules` directory.

## Roles
Roles are present in `roles` directory, you can create new role which uses other roles.

## Playbooks
Sample playbooks can be found in the docs dir.

## Installation

Clone the repo and execute:
```bash
poetry shell #in js-sdk env
pip3 install ansible #if you don't have ansible

cd <js-ansible-modules repo dir>
ansible-galaxy collection build
ansible-galaxy collection install threefold-jsgrid-0.1.0.tar.gz
```
## Run modules and roles
In `docs` dir there are two dirs [ `modules`, `roles` ], they have all `modules` and `roles` playbooks for testing.
  
  **HINT :** Don't forget to change the params [identities, pool ids, etc... ]
  
  ### *Example:*
  ```bash
  ansible-playbook docs/modules/identity/play.yml
  ```

  You can have a look on ansible docs [here](https://docs.ansible.com)