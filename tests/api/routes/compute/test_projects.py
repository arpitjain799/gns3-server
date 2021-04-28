# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 GNS3 Technologies Inc.
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

import pytest
import uuid
import os

from unittest.mock import patch
from tests.utils import asyncio_patch
from fastapi import FastAPI, status
from httpx import AsyncClient

from gns3server.compute.project_manager import ProjectManager
from gns3server.compute.project import Project

pytestmark = pytest.mark.asyncio


@pytest.fixture
def base_params(tmpdir) -> dict:
    """Return standard parameters"""

    params = {
        "name": "test",
        "path": str(tmpdir),
        "project_id": str(uuid.uuid4())
    }
    return params


async def test_create_project_with_path(app: FastAPI, client: AsyncClient, base_params: dict) -> None:

    with patch("gns3server.compute.project.Project.is_local", return_value=True):
        response = await client.post(app.url_path_for("create_compute_project"), json=base_params)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["project_id"] == base_params["project_id"]


async def test_create_project_with_path_and_empty_variables(app: FastAPI,
                                                            client: AsyncClient,
                                                            base_params: dict) -> None:

    base_params["variables"] = None
    with patch("gns3server.compute.project.Project.is_local", return_value=True):

        response = await client.post(app.url_path_for("create_compute_project"), json=base_params)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["project_id"] == base_params["project_id"]


async def test_create_project_without_dir(app: FastAPI, client: AsyncClient, base_params: dict) -> None:

    del base_params["path"]
    response = await client.post(app.url_path_for("create_compute_project"), json=base_params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["project_id"] == base_params["project_id"]
    assert response.json()["name"] == base_params["name"]


async def test_show_project(app: FastAPI, client: AsyncClient, base_params: dict) -> None:

    response = await client.post(app.url_path_for("create_compute_project"), json=base_params)
    assert response.status_code == status.HTTP_201_CREATED
    response = await client.get(app.url_path_for("get_compute_project", project_id=base_params["project_id"]))

    #print(response.json().keys())
    #assert len(response.json().keys()) == 3
    assert response.json()["project_id"] == base_params["project_id"]
    assert response.json()["name"] == base_params["name"]
    assert response.json()["variables"] is None


async def test_show_project_invalid_uuid(app: FastAPI, client: AsyncClient) -> None:

    response = await client.get(app.url_path_for("get_compute_project",
                                                 project_id="50010203-0405-0607-0809-0a0b0c0d0e42"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_list_projects(app: FastAPI, client: AsyncClient) -> dict:

    ProjectManager.instance()._projects = {}

    params = {"name": "test", "project_id": "51010203-0405-0607-0809-0a0b0c0d0e0f"}
    response = await client.post(app.url_path_for("create_compute_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED
    params = {"name": "test", "project_id": "52010203-0405-0607-0809-0a0b0c0d0e0b"}
    response = await client.post(app.url_path_for("create_compute_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.get(app.url_path_for("get_compute_projects"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert "51010203-0405-0607-0809-0a0b0c0d0e0f" in [p["project_id"] for p in response.json()]


async def test_delete_project(app: FastAPI, client: AsyncClient, compute_project: Project) -> None:

    with asyncio_patch("gns3server.compute.project.Project.delete", return_value=True) as mock:
        response = await client.delete(app.url_path_for("delete_compute_project", project_id=compute_project.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock.called


async def test_update_project(app: FastAPI, client: AsyncClient, base_params: dict) -> None:

    response = await client.post(app.url_path_for("create_compute_project"), json=base_params)
    assert response.status_code == status.HTTP_201_CREATED

    params = {"variables": [{"name": "TEST1", "value": "VAL1"}]}
    response = await client.put(app.url_path_for("update_compute_project", project_id=base_params["project_id"]),
                                json=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["variables"] == [{"name": "TEST1", "value": "VAL1"}]


async def test_delete_project_invalid_uuid(app: FastAPI, client: AsyncClient) -> None:

    response = await client.delete(app.url_path_for("delete_compute_project", project_id=str(uuid.uuid4())))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_close_project(app: FastAPI, client: AsyncClient, compute_project: Project) -> None:

    with asyncio_patch("gns3server.compute.project.Project.close", return_value=True) as mock:
        response = await client.post(app.url_path_for("close_compute_project", project_id=compute_project.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock.called


# @pytest.mark.asyncio
# async def test_close_project_two_client_connected(compute_api, compute_project):
#
#     ProjectHandler._notifications_listening = {compute_project.id: 2}
#     with asyncio_patch("gns3server.compute.project.Project.close", return_value=True) as mock:
#         response = await client.post("/projects/{project_id}/close".format(project_id=compute_project.id))
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not mock.called


async def test_close_project_invalid_uuid(app: FastAPI, client: AsyncClient) -> None:

    response = await client.post(app.url_path_for("close_compute_project", project_id=str(uuid.uuid4())))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_file(app: FastAPI, client: AsyncClient, config, tmpdir) -> None:

    config.settings.Server.projects_path = str(tmpdir)
    project = ProjectManager.instance().create_project(project_id="01010203-0405-0607-0809-0a0b0c0d0e0b")

    with open(os.path.join(project.path, "hello"), "w+") as f:
        f.write("world")

    response = await client.get(app.url_path_for("get_compute_project_file", project_id=project.id, file_path="hello"))
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"world"

    response = await client.get(app.url_path_for("get_compute_project_file", project_id=project.id, file_path="false"))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.get(app.url_path_for("get_compute_project_file",
                                                 project_id=project.id,
                                                 file_path="../hello"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_write_file(app: FastAPI, client: AsyncClient, config, tmpdir) -> None:

    config.settings.Server.projects_path = str(tmpdir)
    project = ProjectManager.instance().create_project(project_id="01010203-0405-0607-0809-0a0b0c0d0e0b")

    response = await client.post(app.url_path_for("write_compute_project_file",
                                                  project_id=project.id,
                                                  file_path="hello"), content=b"world")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    with open(os.path.join(project.path, "hello")) as f:
        assert f.read() == "world"

    response = await client.post(app.url_path_for("write_compute_project_file",
                                                  project_id=project.id,
                                                  file_path="../hello"))
    assert response.status_code == status.HTTP_404_NOT_FOUND