#!/usr/bin/env python
#
# Copyright (C) 2016 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import asyncio
import uuid


class VM:

    def __init__(self, project, hypervisor, vm_id=None, vm_type=None, name=None, console=None, console_type="telnet", properties={}):
        """
        :param project: Project of the VM
        :param hypervisor: Hypervisor server where the server will run
        :param vm_id: UUID of the vm. Integer id
        :param vm_type: Type of emulator
        :param name: Name of the vm
        :param console: TCP port of the console
        :param console_type: Type of the console (telnet, vnc, serial..)
        :param properties: Emulator specific properties of the VM
        """

        if vm_id is None:
            self._id = str(uuid.uuid4())
        else:
            self._id = vm_id

        self._name = name
        self._project = project
        self._hypervisor = hypervisor
        self._vm_type = vm_type
        self._console = console
        self._console_type = console_type
        self._properties = properties

    @property
    def id(self):
        return self._id

    @property
    def vm_type(self):
        return self._vm_type

    @property
    def console(self):
        return self._console

    @property
    def console_type(self):
        return self._console_type

    @property
    def properties(self):
        return self._properties

    @property
    def project(self):
        return self._project

    @asyncio.coroutine
    def create(self):
        data = self._properties
        data["vm_id"] = self._id
        data["name"] = self._name
        data["console"] = self._console
        data["console_type"] = self._console_type
        yield from self._hypervisor.post("/projects/{}/{}/vms".format(self._project.id, self._vm_type), data=data)

    def __json__(self):
        return {
            "hypervisor_id": self._hypervisor.id,
            "project_id": self._project.id,
            "vm_id": self._id,
            "vm_type": self._vm_type,
            "name": self._name,
            "console": self._console,
            "console_type": self._console_type,
            "properties": self._properties
        }
