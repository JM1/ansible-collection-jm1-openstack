#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on openstack.cloud.image module written by Hewlett-Packard Development Company, L.P. et al.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---

module: image_import

short_description: Import images into OpenStack image repository.

description:
    - "This module allows one to import images into the OpenStack image repository.
       It is based on Ansible module openstack.cloud.image module from Hewlett-Packard Development Company, L.P. et al."

requirements:
   - backports.tempfile (python 2 only)

options:
    checksum:
        description:
            - "Optional image checksum."
        required: false
        type: str
    format:
        aliases: [ disk_format ]
        description:
            - "Image file format, e.g. raw or qcow2, defaulting to image extension."
        required: false
        type: str
    id:
        description:
            - "Image ID"
        required: false
        type: str
    name:
        description:
            - "Name of the new image, defaulting to filename component of C(uri)."
        required: false
        type: str
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the image be present or absent."
        type: str
    uri:
        description:
            - "File path (relative or absolute) or URL. Required if C(state) is C(present)."
        required: true
        type: str

notes:
  - "No modifications are applied to existing images; module is skipped if image with the same name exists already."

extends_documentation_fragment:
  - openstack.cloud.openstack

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- jm1.openstack.image_import:
    auth:
      auth_url: https://identity.example.com
      username: admin
      password: passme
      project_name: admin
      openstack.cloud.identity_user_domain_name: Default
      openstack.cloud.project_domain_name: Default
    uri: 'https://cdimage.debian.org/cdimage/openstack/archive/10.4.2-20200608/debian-10.4.2-20200608-openstack-amd64.qcow2'
    checksum: 'sha256:00f76f2fd8e3d74c4f0de7cf97cb7b1706be4299ad44a452849e7993757a8549'
'''

RETURN = r'''
id:
    description: ID of the image
    returned: changed or success
    type: str
    sample: '1961709b-64c0-4823-85a8-1f7e8b9eb80c'

name:
    description: Name of the image
    returned: changed or success
    type: str
    sample: 'debian-10.4.1-20200515-openstack-amd64.qcow2'

size:
    description: Size of the image
    returned: changed or success
    type: int
    sample: 536392192

format:
    description: Format of the image
    returned: changed or success
    type: str
    sample: 'qcow2'
'''

# NOTE: Synchronize imports with DOCUMENTATION string above
from ansible.module_utils.openstack import (openstack_full_argument_spec, openstack_cloud_from_module)
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.module_utils.urls import open_url
import ansible.module_utils.six as six
import os
import re
import shutil
import traceback

if six.PY2:
    try:
        from backports import tempfile
    except ImportError:
        BACKPORTS_TEMPFILE_IMPORT_ERROR = traceback.format_exc()
        HAS_BACKPORTS_TEMPFILE = False
    else:
        BACKPORTS_TEMPFILE_IMPORT_ERROR = None
        HAS_BACKPORTS_TEMPFILE = True
elif six.PY3:
    import tempfile


def import_from_disk(
        algorithm,
        checksum,
        format,
        id,
        name,
        state,
        timeout,
        path,
        wait,
        module, sdk, cloud):
    # Upload image to OpenStack image repository

    if not os.path.exists(path):
        raise Exception('Image path %s does not exist' % path)

    if checksum:
        # Verify image checksum
        checksum_on_disk = module.digest_from_file(path, algorithm)
        if checksum != checksum_on_disk:
            raise Exception('Checksum mismatch %s != %s' % (checksum, checksum_on_disk))

    name_or_id = id if id else name
    image = cloud.get_image(name_or_id=name_or_id)
    if image:
        # Fail if image exists already
        raise Exception('image %s exists already' % name_or_id)

    size_on_disk = os.path.getsize(path)

    kwargs = {}
    if id:
        kwargs['id'] = id

    if algorithm in ['md5', 'sha256']:
        kwargs['validate_checksum'] = True
        kwargs[algorithm] = checksum

    image = cloud.create_image(
        name=name,
        filename=path,
        disk_format=format,
        wait=wait,
        timeout=timeout,
        **kwargs)

    if image.size != size_on_disk:
        module.log('[DEBUG] image size on disk is %s, but the uploaded size is %s' % (size_on_disk, image.size))

    return image.id, image.size


def import_(algorithm,
            checksum,
            format,
            id,
            name,
            state,
            timeout,
            uri,
            wait,
            module, sdk, cloud):

    uri_scheme = urlsplit(uri).scheme
    uri_is_url = uri_scheme != 'file' and len(uri_scheme) > 0

    if uri_is_url:
        # Download image from uri and upload image to OpenStack image repository
        with tempfile.TemporaryDirectory() as dir:
            with open_url(uri) as r:
                filename = None

                cd = r.getheader('Content-Disposition')
                if cd:
                    try:
                        filename = re.findall("filename=(.+)", cd)[0]
                    except IndexError:
                        filename = None

                if not filename:
                    filename = os.path.basename(urlsplit(uri).path)

                if not filename:
                    filename = name

                if not name:
                    name = filename

                if not filename:  # or not name
                    raise ValueError('no name given and name could not be derived from uri')

                if not format:
                    format = os.path.splitext(name)[-1]
                    if format and len(format) > 1:
                        # remove leading dot
                        format = format[1:]

                if not format:
                    raise ValueError('no format given and format could not be derived from uri')

                name_or_id = id if id else name
                image = cloud.get_image(name_or_id=name_or_id)

                if image:
                    # image exists already
                    size = image.size
                    format = image.disk_format
                    id = image.id
                    name = image.name
                    return False, id, name, size, format

                # Download image
                local_image_path = os.path.join(dir, filename)
                with open(local_image_path, 'wb') as f:
                    shutil.copyfileobj(r, f)

            id, size = import_from_disk(
                algorithm,
                checksum,
                format,
                id,
                name,
                state,
                timeout,
                local_image_path,
                wait,
                module, sdk, cloud)

            return True, id, name, size, format

    else:  # not uri_is_url
        name_or_id = id if id else name
        if not name_or_id:
            name = os.path.basename(uri)

            if not name:
                raise ValueError('no image name given and image name could not be derived from uri')

            name_or_id = name

        image = cloud.get_image(name_or_id=name_or_id)

        if image:
            # image exists already
            size = image.size
            format = image.disk_format
            id = image.id
            name = image.name
            return False, id, name, size, format

        if not format:
            format = os.path.splitext(name)[-1]
            if format and len(format) > 1:
                # remove leading dot
                format = format[1:]

        if not format:
            raise ValueError('no image format given and format could not be derived from uri')

        id, size = import_from_disk(
            algorithm,
            checksum,
            format,
            id,
            name,
            state,
            timeout,
            uri,
            wait,
            module, sdk, cloud)

        return True, id, name, size, format


def delete(algorithm,
           checksum,
           format,
           id,
           name,
           state,
           timeout,
           uri,
           wait,
           module, sdk, cloud):
    name_or_id = id if id else name

    if not name_or_id:  # no id or name given
        uri_scheme = urlsplit(uri).scheme
        uri_is_url = uri_scheme != 'file' and len(uri_scheme) > 0

        if uri_is_url:
            raise ValueError('name is required for deleting images if uri is given as an url')

        name = os.path.basename(uri)

        if not name:
            raise ValueError('name is required for deleting images')

        name_or_id = name

    image = cloud.get_image(name_or_id=name_or_id)

    if not image:
        # image absent already
        return False, id, name, None, None

    size = image.size
    format = image.disk_format
    id = image.id
    name = image.name

    cloud.delete_image(
        name_or_id,
        wait=wait,
        timeout=timeout)

    return True, id, name, size, format


def core(module):
    sdk, cloud = openstack_cloud_from_module(module)

    checksum = module.params['checksum']
    format = module.params['format']
    id = module.params['id']
    name = module.params['name']
    state = module.params['state']
    timeout = module.params['timeout']
    uri = module.params['uri']
    wait = module.params['wait']

    if checksum:
        try:
            algorithm, checksum = checksum.split(':', 1)
        except ValueError:
            module.fail_json(msg="The checksum parameter has to be in format <algorithm>:<checksum>")
    else:
        algorithm = None
        checksum = None

    if module.check_mode:
        return dict(
            changed=False,
            checksum="%s:%s" % (algorithm, checksum) if checksum is not None else None,
            format=format,
            id=id,
            name=name,
            state=state,
            timeout=timeout,
            uri=uri,
            wait=wait)

    if state == 'present':
        changed, id, name, size, format = import_(
            algorithm,
            checksum,
            format,
            id,
            name,
            state,
            timeout,
            uri,
            wait,
            module, sdk, cloud)
    elif state == 'absent':
        changed, id, name, size, format = delete(
            algorithm,
            checksum,
            format,
            id,
            name,
            state,
            timeout,
            uri,
            wait,
            module, sdk, cloud)

    return dict(
        changed=changed,
        size=(int(size) if size is not None else None),
        checksum="%s:%s" % (algorithm, checksum) if checksum is not None else None,
        format=format,
        id=id,
        name=name,
        state=state,
        timeout=timeout,
        uri=uri,
        wait=wait
    )


def main():
    module = AnsibleModule(
        argument_spec=openstack_full_argument_spec(
            checksum=dict(type='str'),
            format=dict(type='str'),
            id=dict(type='str'),
            name=dict(type='str'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(type='str'),
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['uri']]
        ]
    )

    if six.PY2 and not HAS_BACKPORTS_TEMPFILE:
        module.fail_json(msg=missing_required_lib("backports.tempfile"), exception=BACKPORTS_TEMPFILE_IMPORT_ERROR)

    try:
        result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
