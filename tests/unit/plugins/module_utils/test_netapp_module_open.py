# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2021, Laurent Nicolas <laurentn@netapp.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" unit tests for module_utils netapp_module.py

    Provides utility functions for cloudmanager REST APIs
"""

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import pytest
import sys

from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch
from ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module import NetAppModule

if sys.version_info < (3, 5):
    pytestmark = pytest.mark.skip('skipping as builtins not defined for 2.6 and 2.7')


@patch('builtins.open')
def test_certificates(open):
    open.return_value = OPEN(data=b'1234')
    helper = NetAppModule()
    assert helper.encode_certificates('test') == ('MTIzNA==', None)
    open.return_value = OPEN(data=b'')
    helper = NetAppModule()
    assert helper.encode_certificates('test') == (None, 'Error: file is empty')
    open.return_value = OPEN(raise_exception=True)
    helper = NetAppModule()
    assert helper.encode_certificates('test') == (None, 'intentional error')


class OPEN:
    '''we could use mock_open but I'm not sure it's available in every python version '''
    def __init__(self, data=b'abcd', raise_exception=False):
        self.data = data
        self.raise_exception = raise_exception

    def read(self):
        return self.data
    # the following two methods are associated with "with" in with open ...

    def __enter__(self):
        if self.raise_exception:
            raise OSError('intentional error')
        return self

    def __exit__(self, *args):
        pass
