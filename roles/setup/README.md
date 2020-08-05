# Ansible Role: jm1.openstack.setup

This role helps to install necessary tools and libraries for all roles and modules in collection
[jm1.openstack](https://galaxy.ansible.com/jm1/openstack).

**NOTE:** This role will *not* fetch and install any Ansible role or collection, because Ansible preloads all modules,
roles and tasks etc. before it executes any of them. Please make sure that all necessary roles and collections are
installed before running Ansible. To do so, you may follow the steps described in [`README.md`](https://github.com/JM1/ansible-collection-openstack/blob/master/README.md)
using the provided [`requirements.yml`](https://github.com/JM1/ansible-collection-openstack/blob/master/requirements.yml).

**Tested OS images**
- Cloud image of [`Debian 10 (Buster)` \[`amd64`\]](https://cdimage.debian.org/cdimage/openstack/current/)
- Ubuntu cloud image of [`Ubuntu 20.04 LTS (Focal Fossa)` \[`amd64`\]](https://cloud-images.ubuntu.com/focal/)

Available on Ansible Galaxy in Collection [jm1.openstack](https://galaxy.ansible.com/jm1/openstack).

## Requirements

Module `jm1.pkg.meta_pkg` from Collection [`jm1.pkg`](https://galaxy.ansible.com/jm1/pkg) is used to satisfy all package
dependencies of this Collection [jm1.openstack](https://galaxy.ansible.com/jm1/openstack). To install `jm1.pkg.meta_pkg` you
may follow the steps described in [`README.md`](https://github.com/JM1/ansible-collection-openstack/blob/master/README.md)
using the provided [`requirements.yml`](https://github.com/JM1/ansible-collection-openstack/blob/master/requirements.yml).

## Variables

None.

## Dependencies

| Name            | Description                                                                         |
| --------------- | ----------------------------------------------------------------------------------- |
| `jm1.common`    | Provides `distribution_id` fact which is used to choose OS-specific defaults        |
| `jm1.pkg.setup` | Installs necessary software for module `jm1.pkg.meta_pkg` from collection `jm1.pkg` |

## Example Playbook

```
- hosts: all
  tasks:
    - name: Satisfy software requirements
      import_role:
        name: jm1.openstack.setup
```

For instructions on how to run Ansible playbooks have look at Ansible's
[Getting Started Guide](https://docs.ansible.com/ansible/latest/network/getting_started/first_playbook.html).

## License

GPL3

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
