# Ansible Role `jm1.openstack.setup`

This role helps to install necessary tools and libraries for all roles and modules in collection [`jm1.openstack`][
galaxy-jm1-openstack].

[galaxy-jm1-openstack]: https://galaxy.ansible.com/jm1/openstack

**NOTE:** This role will *not* fetch and install any Ansible role or collection, because Ansible preloads all modules,
roles and tasks etc. before it executes any of them. Please make sure that all necessary roles and collections are
installed before running Ansible. To do so, you may follow the steps described in [`README.md`][jm1-openstack-readme]
using the provided [`requirements.yml`][jm1-openstack-requirements].

**Tested OS images**
- Generic cloud image of [`CentOS 7 (Core)` \[`amd64`\]](https://cloud.centos.org/centos/7/images/)
- Generic cloud image of [`CentOS 8 (Stream)` \[`amd64`\]](https://cloud.centos.org/centos/8-stream/x86_64/images/)
- Generic cloud image of [`CentOS 9 (Stream)` \[`amd64`\]](https://cloud.centos.org/centos/9-stream/x86_64/images/)
- Cloud image of [`Debian 10 (Buster)` \[`amd64`\]](https://cdimage.debian.org/images/cloud/buster/daily/)
- Cloud image of [`Debian 11 (Bullseye)` \[`amd64`\]](https://cdimage.debian.org/images/cloud/bullseye/daily/)
- Cloud image of [`Debian 12 (Bookworm)` \[`amd64`\]](https://cdimage.debian.org/images/cloud/bookworm/daily/)
- Ubuntu cloud image of [`Ubuntu 20.04 LTS (Focal Fossa)` \[`amd64`\]](https://cloud-images.ubuntu.com/focal/)
- Ubuntu cloud image of [`Ubuntu 22.04 LTS (Jammy Jellyfish)` \[`amd64`\]](https://cloud-images.ubuntu.com/jammy/)
- Ubuntu cloud image of [`Ubuntu 22.04 LTS (Jammy Jellyfish)` \[`amd64`\]](https://cloud-images.ubuntu.com/jammy/)

Available on Ansible Galaxy in Collection [jm1.openstack](https://galaxy.ansible.com/jm1/openstack).

## Requirements

This role uses module `jm1.pkg.meta_pkg` from collection [`jm1.pkg`][galaxy-jm1-pkg]. To install this collection you may
follow the steps described in [`README.md`][jm1-openstack-readme] using the provided [`requirements.yml`][
jm1-openstack-requirements].

[galaxy-jm1-pkg]: https://galaxy.ansible.com/jm1/pkg
[jm1-openstack-readme]: ../../README.md
[jm1-openstack-requirements]: ../../requirements.yml

## Variables

| Name               | Default value                 | Required | Description                                                                                               |
| ------------------ | ----------------------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `distribution_id`  | *depends on operating system* | false    | List which uniquely identifies a distribution release, e.g. `[ 'Debian', '10' ]` for `Debian 10 (Buster)` |

## Dependencies

| Name            | Description                                                                         |
| --------------- | ----------------------------------------------------------------------------------- |
| `jm1.pkg.setup` | Installs necessary software for module `jm1.pkg.meta_pkg` from collection `jm1.pkg` |

## Example Playbook

```yml
- hosts: all
  become: true
  roles:
  - name: Satisfy software requirements
    role: jm1.openstack.setup
    tags: ["jm1.openstack.setup"]
```

For instructions on how to run Ansible playbooks have look at Ansible's
[Getting Started Guide](https://docs.ansible.com/ansible/latest/network/getting_started/first_playbook.html).

## License

GNU General Public License v3.0 or later

See [LICENSE.md](../../LICENSE.md) to see the full text.

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
