# Ansible Role `jm1.openstack.cloud`

This role helps with managing [OpenStack][openstack] resources from Ansible variables.

It allows to

* add and remove [Nova (Compute) flavors][openstack-nova-flavors],
* add and remove [OpenStack Glance images][openstack-images] and define [image properties][openstack-image-properties],
* create and delete [SSH keys][openstack-cli-keypair] and [security groups and security group rules in OpenStack
  Neutron][neutron-security-groups] in [OpenStack projects][openstack-ops-guide-projects-users] to [configure access and
  security for OpenStack Compute instances][horizon-access],
* create, modify and delete [Neutron resources][neutron-admin-guide] such as [networks, subnets, routers, ports and
  floating ips][neutron-intro],
* managing the [state][server-concepts] of [OpenStack Nova (Compute) instances][nova], i.e. start, pause, suspend,
  shutoff, shelve and offload servers,
* add and remove [OpenStack Cinder (block storage) volumes][cinder-admin],

and much more with variable `cloud_config`.

Role variable `cloud_config` defines a list of tasks which will be run by this role. Each task calls an Ansible module
similar to tasks in roles or playbooks except that only few [keywords][playbooks-keywords] such as `register` and `when`
are supported.

For example, to add a flavor with name `m1.tiny`, 1 VCPU, 512MB RAM and a 1GB Disk to [OpenStack project `admin`][
openstack-ops-guide-projects-users], first define variable `cloud_config` with [`openstack.cloud.compute_flavor`][
openstack-cloud-compute-flavor] in [`group_vars` or `host_vars`][ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.compute_flavor:
    vcpus: 1
    disk: 1
    ephemeral: 0
    extra_specs: {}
    flavorid: auto
    is_public: yes
    name: 'm1.tiny'
    projects:
    - name: 'admin'
      state: present
    ram: 512
    rxtx_factor: '1.0'
    swap: 0
    state: present
```

To add an image of Debian 11 (Bullseye) instead, define variable `openstack_images` with [`jm1.openstack.image_import`][
jm1-openstack-image-import] in [`group_vars` or `host_vars`][ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.image:
    # no checksum because image is updated every week
    name: debian-11-genericcloud-amd64
    properties:
      cpu_arch: x86_64
      hw_disk_bus: virtio
      hw_qemu_guest_agent: 'yes'
      hw_video_model: qxl
      hw_vif_model: virtio
      os_distro: debian
      os_require_quiesce: 'yes'
      os_version: 11
    state: present
    uri: https://cdimage.debian.org/images/cloud/bullseye/latest/debian-11-genericcloud-amd64.raw
```

To ensure that the public SSH (RSA) key of the current user who runs Ansible on the Ansible controller is present,
define variable `cloud_config` with [`openstack.cloud.keypair`][openstack-cloud-keypair] in
[`group_vars` or `host_vars`][ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.keypair:
    comment: >-
      {{ lookup('pipe','whoami') + '@' + lookup('pipe','hostname') + ':' + lookup('env','HOME') + '/.ssh/id_rsa.pub' }}
    key: "{{ lookup('file', lookup('env','HOME') + '/.ssh/id_rsa.pub')|mandatory }}"
    state: present
    user: '{{ ansible_user }}'
```


To add an externally accessible network `external_network`, define variable `cloud_config` with [`openstack.cloud.network`][
openstack-cloud-network] in [`group_vars` or `host_vars`][ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.network:
     external: true
    name: external_network
    state: present
```

To create a security group `default` which allows all
outgoing IPv4 / IPv6 traffic and incoming IPv4 / IPv6 traffic between instances in this security group, define variable
`cloud_config` with [`openstack.cloud.security_group`][openstack-cloud-security-group] in [`group_vars` or `host_vars`][
ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.security_group:
    name: default
    description: 'Allow outgoing and internal IPv4 and IPv6 traffic'
    rules:
    - direction: 'egress'
      ethertype: 'IPv4'
      state: present
    - direction: 'egress'
      ethertype: 'IPv6'
      state: present
    - direction: 'ingress'
      ethertype: 'IPv4'
      remote_group: 'default'
      state: present
    - direction: 'ingress'
      ethertype: 'IPv6'
      remote_group: 'default'
      state: present
    state: present
```

To shutdown compute instance `debian.home.arpa`, define `cloud_config` with [`openstack.cloud.server_action`][
openstack-cloud-server-action] in [`group_vars` or `host_vars`][ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.server_action:
    action: stop
    server: 'debian.home.arpa'
```

To create a new 20GB volume based on an existing image `debian-11-genericcloud-amd64`, define variable
`cloud_config` with  [`openstack.cloud.volume`][openstack-cloud-volume] in [`group_vars` or `host_vars`][
ansible-inventory] as such:

```yml
cloud_config:
- openstack.cloud.volume:
    bootable: yes
    display_name: '{{ inventory_hostname }}'
    image: 'debian-11-genericcloud-amd64'
    size: 20
    state: present
```

Next, provide [OpenStack auth information for the OpenStack SDK][openstacksdk-config], i.e. define [module defaults][
ansible-module-defaults] in playbooks or define OpenStack `OS_*` environment variables. For example, create file
`$HOME/.config/openstack/clouds.yaml` with

```yml
clouds:
  admin_devstack_home_arpa:
    profile: devstack_home_arpa
    auth:
      username: admin
      project_name: admin
      password: secret
```

and `$HOME/.config/openstack/clouds-public.yaml` with

```yml
public-clouds:
  devstack_home_arpa:
    auth:
      auth_url: http://devstack.home.arpa:5000/v3/
      user_domain_name: Default
      project_domain_name: Default
    block_storage_api_version: 3
    identity_api_version: 3
    volume_api_version: 3
    interface: internal
    # Workaround for a bug in python-openstackclient where 'interface' key is ignored.
    # The old 'endpoint_type' key is still respected though.
    # Ref.: https://storyboard.openstack.org/#!/story/2007380
    endpoint_type: internal
```

and define a playbook with [module defaults][ansible-module-defaults] as such:

```yml
- hosts: all
  connection: local # Connection to OpenStack is handled by OpenStack SDK and Ansible's OpenStack modules
  module_defaults:
    group/openstack.cloud.openstack:
      cloud: admin_devstack_home_arpa
  roles:
  - role: jm1.openstack.cloud
    tags: ["jm1.openstack.cloud"]
```

When this role is executed, it will pass each item of the `cloud_config` list one after another as parameters to module
[`jm1.ansible.execute_module`][jm1-ansible-execute-module] from collection [`jm1.ansible`][galaxy-jm1-ansible].

[ansible-inventory]: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
[ansible-module-defaults]: https://docs.ansible.com/ansible/latest/user_guide/playbooks_module_defaults.html
[cinder-admin]: https://docs.openstack.org/cinder/latest/admin/blockstorage-manage-volumes.html
[galaxy-jm1-ansible]: https://galaxy.ansible.com/jm1/ansible
[horizon-access]: https://docs.openstack.org/horizon/latest/user/configure-access-and-security-for-instances.html
[jm1-ansible-execute-module]: https://github.com/JM1/ansible-collection-jm1-ansible/blob/master/plugins/modules/execute_module.py
[jm1-openstack-image-import]: ../../plugins/modules/image_import.py
[neutron-admin-guide]: https://docs.openstack.org/neutron/latest/admin/
[neutron-intro]: https://docs.openstack.org/neutron/latest/admin/intro-os-networking.html
[neutron-security-groups]: https://docs.openstack.org/neutron/latest//admin/archives/adv-features.html#security-groups
[nova]: https://docs.openstack.org/nova/latest/
[openstack]: https://www.openstack.org/
[openstack-cli-keypair]: https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/keypair.html
[openstack-cloud-compute-flavor]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/compute_flavor_module.html
[openstack-cloud-keypair]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/keypair_module.html
[openstack-cloud-network]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/network_module.html
[openstack-cloud-security-group]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/security_group_module.html
[openstack-cloud-server-action]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/server_action_module.html
[openstack-cloud-volume]: https://docs.ansible.com/ansible/latest/collections/openstack/cloud/volume_module.html
[openstack-image-properties]: https://docs.openstack.org/glance/latest/admin/useful-image-properties.html
[openstack-images]: https://docs.openstack.org/glance/latest/admin/manage-images.html
[openstack-nova-flavors]: https://docs.openstack.org/nova/latest/admin/flavors.html
[openstack-ops-guide-projects-users]: https://docs.openstack.org/operations-guide/ops-projects-users.html
[openstacksdk-config]: https://docs.openstack.org/openstacksdk/latest/user/config/configuration.html
[playbooks-keywords]: https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html
[server-concepts]: https://docs.openstack.org/api-guide/compute/server_concepts.html

**Tested OS images**
- Cloud image of [`Debian 10 (Buster)` \[`amd64`\]](https://cdimage.debian.org/cdimage/openstack/current/)
- Cloud image of [`Debian 11 (Bullseye)` \[`amd64`\]](https://cdimage.debian.org/images/cloud/bullseye/latest/)
- Cloud image of [`Debian 12 (Bookworm)` \[`amd64`\]](https://cdimage.debian.org/images/cloud/bookworm/)
- Generic cloud image of [`CentOS 7 (Core)` \[`amd64`\]](https://cloud.centos.org/centos/7/images/)
- Generic cloud image of [`CentOS 8 (Stream)` \[`amd64`\]](https://cloud.centos.org/centos/8-stream/x86_64/images/)
- Generic cloud image of [`CentOS 9 (Stream)` \[`amd64`\]](https://cloud.centos.org/centos/9-stream/x86_64/images/)
- Ubuntu cloud image of [`Ubuntu 18.04 LTS (Bionic Beaver)` \[`amd64`\]](https://cloud-images.ubuntu.com/bionic/current/)
- Ubuntu cloud image of [`Ubuntu 20.04 LTS (Focal Fossa)` \[`amd64`\]](https://cloud-images.ubuntu.com/focal/)
- Ubuntu cloud image of [`Ubuntu 22.04 LTS (Jammy Jellyfish)` \[`amd64`\]](https://cloud-images.ubuntu.com/jammy/)

Available on Ansible Galaxy in Collection [jm1.openstack](https://galaxy.ansible.com/jm1/openstack).

## Requirements

This role uses module(s) from collection [`jm1.ansible`][galaxy-jm1-ansible]. To install this collection you may follow
the steps described in [`README.md`][jm1-openstack-readme] using the provided [`requirements.yml`][
jm1-openstack-requirements].

[galaxy-jm1-ansible]: https://galaxy.ansible.com/jm1/ansible
[jm1-openstack-readme]: ../../README.md
[jm1-openstack-requirements]: ../../requirements.yml

## Variables

| Name           | Default value | Required | Description |
| -------------- | ------------- | -------- | ----------- |
| `cloud_config` | `[]`          | no       | List of tasks to run [^example-modules] [^supported-keywords] [^supported-modules] |

[^supported-modules]: Tasks will be executed with [`jm1.ansible.execute_module`][jm1-ansible-execute-module] which
supports modules and action plugins only. Some Ansible modules such as [`ansible.builtin.meta`][ansible-builtin-meta]
and `ansible.builtin.{include,import}_{playbook,role,tasks}` are core features of Ansible, in fact not implemented as
modules and thus cannot be called from `jm1.ansible.execute_module`. Doing so causes Ansible to raise errors such as
`MODULE FAILURE\nSee stdout/stderr for the exact error`. In addition, Ansible does not support free-form parameters
for arbitrary modules, so for example, change from `- debug: msg=""` to `- debug: { msg: "" }`.

[^supported-keywords]: Tasks will be executed with [`jm1.ansible.execute_module`][jm1-ansible-execute-module] which
supports keywords `register` and `when` only.

[^example-modules]: Useful Ansible modules in this context could be modules such as [`openstack.cloud.server`][
openstack-cloud-server] and other modules from Ansible collection [`openstack.cloud`][galaxy-openstack-cloud].

[ansible-builtin-meta]: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/meta_module.html
[jm1-ansible-execute-module]: https://github.com/JM1/ansible-collection-jm1-ansible/blob/master/plugins/modules/execute_module.py
[galaxy-openstack-cloud]: https://galaxy.ansible.com/openstack/cloud

## Dependencies

None.

## Example Playbook

First, provide [OpenStack auth information for OpenStack SDK][openstacksdk-config]. The following code uses cloud name
`admin_devstack_home_arpa` as defined above.

```yml
- hosts: all
  connection: local # Connection to OpenStack is handled by OpenStack SDK and Ansible's OpenStack modules
  module_defaults:
    group/openstack.cloud.openstack:
      cloud: admin_devstack_home_arpa
  vars:
    # Variables are listed here for convenience and illustration.
    # In a production setup, variables would be defined e.g. in
    # group_vars and/or host_vars of an Ansible inventory.
    # Ref.:
    # https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html
    # https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
    cloud_config:
    - openstack.cloud.compute_flavor:
        vcpus: 1
        disk: 1
        ephemeral: 0
        extra_specs: {}
        flavorid: auto
        is_public: yes
        name: 'm1.tiny'
        projects:
        - name: 'admin'
          state: present
        ram: 512
        rxtx_factor: '1.0'
        swap: 0
        state: present
    - openstack.cloud.image:
        # no checksum because image is updated every week
        name: debian-11-genericcloud-amd64
        properties:
          cpu_arch: x86_64
          hw_disk_bus: virtio
          hw_qemu_guest_agent: 'yes'
          hw_video_model: qxl
          hw_vif_model: virtio
          os_distro: debian
          os_require_quiesce: 'yes'
          os_version: 11
        state: present
        uri: https://cdimage.debian.org/images/cloud/bullseye/latest/debian-11-genericcloud-amd64.raw
    - openstack.cloud.keypair:
        public_key: "{{ lookup('file', lookup('env','HOME') + '/.ssh/id_rsa.pub')|mandatory }}"
        state: present
        user: '{{ ansible_user }}'
    - openstack.cloud.network:
        external: true
        name: external_network
        state: present
    - openstack.cloud.security_group:
        name: default
        description: 'Allow outgoing and internal IPv4 and IPv6 traffic'
        rules:
        - direction: 'egress'
          ethertype: 'IPv4'
          state: present
        - direction: 'egress'
          ethertype: 'IPv6'
          state: present
        - direction: 'ingress'
          ethertype: 'IPv4'
          remote_group: 'default'
          state: present
        - direction: 'ingress'
          ethertype: 'IPv6'
          remote_group: 'default'
          state: present
        state: present
    - openstack.cloud.server_action:
        action: stop
        server: '{{ inventory_hostname }}'
    - openstack.cloud.volume:
        bootable: yes
        display_name: '{{ inventory_hostname }}'
        image: 'debian-11-genericcloud-amd64'
        size: 20
        state: present
  roles:
  - role: jm1.openstack.cloud
    tags: ["jm1.openstack.cloud"]
```

For instructions on how to run Ansible playbooks have look at Ansible's
[Getting Started Guide](https://docs.ansible.com/ansible/latest/network/getting_started/first_playbook.html).

## License

GNU General Public License v3.0 or later

See [LICENSE.md](../../LICENSE.md) to see the full text.

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
