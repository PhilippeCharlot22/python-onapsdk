#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Test Service module."""

from os import path
import shutil

import mock
from unittest.mock import MagicMock
import pytest
import requests

import onapsdk.constants as const
from onapsdk.service import Service
from onapsdk.sdc_resource import SdcResource
from onapsdk.utils.headers_creator import headers_sdc_tester
from onapsdk.utils.headers_creator import headers_sdc_governor
from onapsdk.utils.headers_creator import headers_sdc_operator
from onapsdk.utils.headers_creator import headers_sdc_creator


def test_init_no_name():
    """Check init with no names."""
    svc = Service()
    assert isinstance(svc, SdcResource)
    assert svc._identifier is None
    assert svc._version is None
    assert svc.name == "ONAP-test-Service"
    assert svc.headers["USER_ID"] == "cs0008"
    assert svc.distribution_status is None
    assert svc._distribution_id is None
    assert isinstance(svc._base_url(), str)

@mock.patch.object(Service, 'exists')
def test_init_with_name(mock_exists):
    """Check init with no names."""
    mock_exists.return_value = False
    svc = Service(name="YOLO")
    assert svc._identifier == None
    assert svc._version == None
    assert svc.name == "YOLO"
    assert svc.created() == False
    assert svc.headers["USER_ID"] == "cs0008"
    assert svc.distribution_status is None
    assert svc._distribution_id is None
    assert isinstance(svc._base_url(), str)

@mock.patch.object(Service, 'exists')
def test_init_with_sdc_values(mock_exists):
    """Check init with no names."""
    sdc_values = {'uuid': '12', 'version': '14', 'invariantUUID': '56',
                  'distributionStatus': 'yes', 'lifecycleState': 'state'}
    svc = Service(sdc_values=sdc_values)
    mock_exists.return_value = True
    assert svc._identifier == "12"
    assert svc._version == "14"
    assert svc.name == "ONAP-test-Service"
    assert svc.created()
    assert svc.headers["USER_ID"] == "cs0008"
    assert svc.distribution_status == "yes"
    assert svc._distribution_id is None
    assert isinstance(svc._base_url(), str)

def test_equality_really_equals():
    """Check two vfs are equals if name is the same."""
    svc_1 = Service(name="equal")
    svc_1.identifier = "1234"
    svc_2 = Service(name="equal")
    svc_2.identifier = "1235"
    assert svc_1 == svc_2


def test_equality_not_equals():
    """Check two vfs are not equals if name is not the same."""
    svc_1 = Service(name="equal")
    svc_1.identifier = "1234"
    svc_2 = Service(name="not_equal")
    svc_2.identifier = "1234"
    assert svc_1 != svc_2


def test_equality_not_equals_not_same_object():
    """Check a vf and something different are not equals."""
    svc_1 = Service(name="equal")
    svc_1.identifier = "1234"
    svc_2 = SdcResource()
    svc_2.name = "equal"
    assert svc_1 != svc_2

@mock.patch.object(Service, 'load_metadata')
def test_distribution_id_no_load(mock_load):
    svc = Service()
    svc.identifier = "1234"
    svc._distribution_id = "4567"
    assert svc.distribution_id == "4567"
    mock_load.assert_not_called()

@mock.patch.object(Service, 'load_metadata')
def test_distribution_id_load(mock_load):
    svc = Service()
    svc.identifier = "1234"
    assert svc.distribution_id is None
    mock_load.assert_called_once()

@mock.patch.object(Service, '_check_distributed')
def test_distributed_no_load(mock_check_distributed):
    svc = Service()
    svc.identifier = "1234"
    svc._distributed = True
    assert svc.distributed
    mock_check_distributed.assert_not_called()

@mock.patch.object(Service, '_check_distributed')
def test_distributed_load(mock_check_distributed):
    svc = Service()
    svc.identifier = "1234"
    assert not svc.distributed
    mock_check_distributed.assert_called_once()

def test_distribution_id_setter():
    svc = Service()
    svc.identifier = "1234"
    svc.distribution_id = "4567"
    assert svc._distribution_id == "4567"

@mock.patch.object(Service, '_create')
def test_create(mock_create):
    svc = Service()
    svc.create()
    mock_create.assert_called_once_with("service_create.json.j2", name="ONAP-test-Service")

@mock.patch.object(Service, 'exists')
@mock.patch.object(Service, 'send_message')
def test_add_resource_not_draft(mock_send, mock_exists):
    mock_exists.return_value = False
    svc = Service()
    resource = SdcResource()
    svc.add_resource(resource)
    mock_send.assert_not_called()

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, 'send_message')
def test_add_resource_bad_result(mock_send, mock_load):
    svc = Service()
    svc.unique_identifier = "45"
    svc.identifier = "93"
    svc.status = const.DRAFT
    mock_send.return_value = {}
    resource = SdcResource()
    resource.unique_identifier = "12"
    resource.created = MagicMock(return_value=True)
    resource.version = "40"
    resource.name = "test"
    assert svc.add_resource(resource) is None
    mock_send.assert_called_once_with(
        'POST', 'Add SdcResource to service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/45/resourceInstance',
        data='{\n  "name": "test",\n  "componentVersion": "40",\n  "posY": 100,\n  "posX": 200,\n  "uniqueId": "12",\n  "originType": "SDCRESOURCE",\n  "componentUid": "12",\n  "icon": "defaulticon"\n}')

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, 'send_message')
def test_add_resource_OK(mock_send, mock_load):
    svc = Service()
    svc.unique_identifier = "45"
    svc.identifier = "93"
    svc.status = const.DRAFT
    mock_send.return_value = {'yes': 'indeed'}
    resource = SdcResource()
    resource.unique_identifier = "12"
    resource.created = MagicMock(return_value=True)
    resource.version = "40"
    resource.name = "test"
    result = svc.add_resource(resource)
    assert result['yes'] == "indeed"
    mock_send.assert_called_once_with(
        'POST', 'Add SdcResource to service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/45/resourceInstance',
        data='{\n  "name": "test",\n  "componentVersion": "40",\n  "posY": 100,\n  "posX": 200,\n  "uniqueId": "12",\n  "originType": "SDCRESOURCE",\n  "componentUid": "12",\n  "icon": "defaulticon"\n}')

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_checkin(mock_verify):
    svc = Service()
    svc.checkin()
    mock_verify.assert_called_once_with(const.DRAFT, const.CHECKIN, 'lifecycleState')

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_submit(mock_verify):
    svc = Service()
    svc.submit()
    mock_verify.assert_called_once_with(const.CHECKED_IN, const.SUBMIT_FOR_TESTING, 'lifecycleState')

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_start_certification(mock_verify):
    svc = Service()
    svc.start_certification()
    mock_verify.assert_called_once_with(
        const.SUBMITTED, const.START_CERTIFICATION, 'lifecycleState',
        headers=headers_sdc_tester(svc.headers))

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_certify(mock_verify):
    svc = Service()
    svc.certify()
    mock_verify.assert_called_once_with(
        const.UNDER_CERTIFICATION, const.CERTIFY, 'lifecycleState',
        headers=headers_sdc_tester(svc.headers))

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_approve(mock_verify):
    svc = Service()
    svc.approve()
    mock_verify.assert_called_once_with(
        const.CERTIFIED, const.APPROVE, 'distribution-state',
        headers=headers_sdc_governor(svc.headers))

@mock.patch.object(Service, '_verify_action_to_sdc')
def test_distribute(mock_verify):
    svc = Service()
    svc.distribute()
    mock_verify.assert_called_once_with(
        const.APPROVED, const.DISTRIBUTE, 'distribution',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message')
def test_get_tosca_no_result(mock_send):
    if path.exists('/tmp/tosca_files'):
        shutil.rmtree('/tmp/tosca_files')
    mock_send.return_value = {}
    svc = Service()
    svc.identifier = "12"
    svc.get_tosca()
    headers = headers_sdc_creator(svc.headers)
    headers['Accept'] = 'application/octet-stream'
    mock_send.assert_called_once_with(
        'GET', 'Download Tosca Model for ONAP-test-Service',
        'https://sdc.api.be.simpledemo.onap.org:30204/sdc/v1/catalog/services/12/toscaModel',
        headers=headers)
    assert not path.exists('/tmp/tosca_files')


def test_get_tosca_bad_csart(requests_mock):
    if path.exists('/tmp/tosca_files'):
        shutil.rmtree('/tmp/tosca_files')
    with open('tests/data/bad.csar', mode='rb') as file:
        file_content = file.read()
        requests_mock.get(
            'https://sdc.api.be.simpledemo.onap.org:30204/sdc/v1/catalog/services/12/toscaModel',
            content=file_content)
    svc = Service()
    svc.identifier = "12"
    svc.get_tosca()


def test_get_tosca_result(requests_mock):
    if path.exists('/tmp/tosca_files'):
        shutil.rmtree('/tmp/tosca_files')
    with open('tests/data/test.csar', mode='rb') as file:
        file_content = file.read()
        requests_mock.get(
            'https://sdc.api.be.simpledemo.onap.org:30204/sdc/v1/catalog/services/12/toscaModel',
            content=file_content)
    svc = Service()
    svc.identifier = "12"
    svc.get_tosca()

@mock.patch.object(Service, 'send_message_json')
def test_distributed_no_result(mock_send):
    mock_send.return_value = {}
    svc = Service()
    svc.distribution_id = "12"
    assert not svc.distributed

@mock.patch.object(Service, 'send_message_json')
def test_distributed_not_distributed(mock_send):
    mock_send.return_value = {
        'distributionStatusList':[
            {'omfComponentID': "SO", 'status': "DOWNLOAD_OK"},
            {'omfComponentID': "sdnc", 'status': "DOWNLOAD_NOK"},
            {'omfComponentID': "aai", 'status': "DOWNLOAD_OK"}]}
    svc = Service()
    svc.distribution_id = "12"
    assert not svc.distributed
    mock_send.assert_called_once_with(
        'GET', 'Check distribution for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/distribution/12',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message_json')
def test_distributed_not_distributed(mock_send):
    mock_send.return_value = {
        'distributionStatusList':[
            {'omfComponentID': "SO", 'status': "DOWNLOAD_OK"},
            {'omfComponentID': "aai", 'status': "DOWNLOAD_OK"}]}
    svc = Service()
    svc.distribution_id = "12"
    assert not svc.distributed
    mock_send.assert_called_once_with(
        'GET', 'Check distribution for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/distribution/12',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message_json')
def test_distributed_distributed(mock_send):
    mock_send.return_value = {
        'distributionStatusList':[
            {'omfComponentID': "SO", 'status': "DOWNLOAD_OK"},
            {'omfComponentID': "sdnc", 'status': "DOWNLOAD_OK"},
            {'omfComponentID': "aai", 'status': "DOWNLOAD_OK"}]}
    svc = Service()
    svc.distribution_id = "12"
    assert svc.distributed
    mock_send.assert_called_once_with(
        'GET', 'Check distribution for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/distribution/12',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message_json')
def test_load_metadata_no_result(mock_send):
    mock_send.return_value = {}
    svc = Service()
    svc.identifier = "1"
    svc.load_metadata()
    assert svc._distribution_id is None
    mock_send.assert_called_once_with(
        'GET', 'Get Metadata for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/1/distribution',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message_json')
def test_load_metadata_bad_json(mock_send):
    mock_send.return_value = {'yolo': 'in the wood'}
    svc = Service()
    svc.identifier = "1"
    svc.load_metadata()
    assert svc._distribution_id is None
    mock_send.assert_called_once_with(
        'GET', 'Get Metadata for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/1/distribution',
        headers=headers_sdc_operator(svc.headers))

@mock.patch.object(Service, 'send_message_json')
def test_load_metadata_OK(mock_send):
    mock_send.return_value = {'distributionStatusOfServiceList': [
        {'distributionID': "11"}, {'distributionID': "12"}]}
    svc = Service()
    svc.identifier = "1"
    svc.load_metadata()
    assert svc._distribution_id == "12"
    mock_send.assert_called_once_with(
        'GET', 'Get Metadata for ONAP-test-Service',
        'https://sdc.api.fe.simpledemo.onap.org:30207/sdc1/feProxy/rest/v1/catalog/services/1/distribution',
        headers=headers_sdc_operator(svc.headers))

def test_get_all_url():
    assert Service._get_all_url() == "https://sdc.api.be.simpledemo.onap.org:30204/sdc/v1/catalog/services"

@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'load')
def test_really_submit_no_results(mock_load, mock_action):
    mock_action.return_value = {}
    svc = Service()
    svc._really_submit()
    mock_load.assert_not_called()
    mock_action.assert_called_once_with('Certify', action_type='lifecycleState')

@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'load')
def test_really_submit_OK(mock_load, mock_action):
    mock_action.return_value = "yes"
    svc = Service()
    svc._really_submit()
    mock_load.assert_called_once()
    mock_action.assert_called_once_with('Certify', action_type='lifecycleState')

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'created')
def test_verify_action_to_sdc_not_created(mock_created, mock_action, mock_load):
    mock_created.return_value = False
    svc = Service()
    svc._status = "no_yes"
    svc._verify_action_to_sdc("yes", "action", action_type='lifecycleState')
    mock_created.assert_called()
    mock_action.assert_not_called()
    mock_load.assert_not_called()

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'created')
def test_verify_action_to_sdc_bad_status(mock_created, mock_action, mock_load):
    mock_created.return_value = True
    svc = Service()
    svc._status = "no_yes"
    svc._verify_action_to_sdc("yes", "action", action_type='lifecycleState')
    mock_created.assert_called()
    mock_action.assert_not_called()
    mock_load.assert_not_called()

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'created')
def test_verify_action_to_sdc_no_result(mock_created, mock_action, mock_load):
    mock_created.return_value = True
    mock_action.return_value = {}
    svc = Service()
    svc._status = "no_yes"
    svc._verify_action_to_sdc("yes", "action", action_type='lifecycleState')
    mock_created.assert_called()
    mock_action.assert_not_called()
    mock_load.assert_not_called()

@mock.patch.object(Service, 'load')
@mock.patch.object(Service, '_action_to_sdc')
@mock.patch.object(Service, 'created')
def test_verify_action_to_sdc_OK(mock_created, mock_action, mock_load):
    mock_created.return_value = True
    mock_action.return_value = "good"
    svc = Service()
    svc._status = "yes"
    svc._verify_action_to_sdc("yes", "action", action_type='lifecycleState')
    mock_created.assert_called()
    mock_action.assert_called_once()
    mock_load.assert_called_once()