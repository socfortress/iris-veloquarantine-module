#!/usr/bin/env python3
#
#
#  IRIS veloquarantine Source Code
#  Copyright (C) 2023 - SOCFortress
#  info@socfortress.co
#  Created by SOCFortress - 2023-01-30
#
#  License MIT


import traceback
from jinja2 import Template

import json
import time

# Imports for datastore handling
import grpc
import iris_interface.IrisInterfaceStatus as InterfaceStatus
import pyvelociraptor
from pyvelociraptor import api_pb2, api_pb2_grpc


class VeloquarantineHandler(object):
    def __init__(self, mod_config, server_config, logger):
        self.mod_config = mod_config
        self.server_config = server_config
        self.veloquarantine = self.get_veloquarantine_instance()
        self.log = logger
        self.config = pyvelociraptor.LoadConfigFile(self.mod_config.get('velo_api_config'))

    def get_veloquarantine_instance(self):
        """
        Returns an veloquarantine API instance depending if the key is premium or not

        :return: { cookiecutter.keyword }} Instance
        """
        url = self.mod_config.get('veloquarantine_url')
        key = self.mod_config.get('veloquarantine_key')
        proxies = {}

        if self.server_config.get('http_proxy'):
            proxies['https'] = self.server_config.get('HTTPS_PROXY')

        if self.server_config.get('https_proxy'):
            proxies['http'] = self.server_config.get('HTTP_PROXY')

        # TODO!
        # Here get your veloquarantine instance and return it
        # ex: return veloquarantineApi(url, key)
        return "<TODO>"

    def gen_domain_report_from_template(self, html_template, veloquarantine_report) -> InterfaceStatus:
        """
        Generates an HTML report for Domain, displayed as an attribute in the IOC

        :param html_template: A string representing the HTML template
        :param misp_report: The JSON report fetched with veloquarantine API
        :return: InterfaceStatus
        """
        template = Template(html_template)
        context = veloquarantine_report
        pre_render = dict({"results": []})

        for veloquarantine_result in context:
            pre_render["results"].append(veloquarantine_result)

        try:
            rendered = template.render(pre_render)

        except Exception:
            print(traceback.format_exc())
            log.error(traceback.format_exc())
            return InterfaceStatus.I2Error(traceback.format_exc())

        return InterfaceStatus.I2Success(data=rendered)

    def handle_windows(self, asset):
        """
        Handles an Asset and Quarantines the endpoint via Velociraptor
        :param asset: ASSET instance
        :return: IIStatus
        """

        self.log.info(f"Running Quarantine for {asset.asset_name}")

        creds = grpc.ssl_channel_credentials(
            root_certificates=self.config["ca_certificate"].encode("utf8"),
            private_key=self.config["client_private_key"].encode("utf8"),
            certificate_chain=self.config["client_cert"].encode("utf8"),
        )

        options = (("grpc.ssl_target_name_override", "VelociraptorServer"),)

        with grpc.secure_channel(
            self.config["api_connection_string"],
            creds,
            options,
        ) as channel:
            stub = api_pb2_grpc.APIStub(channel)

            client_query = (
                "select client_id from clients(search='host:" + asset.asset_name + "')"
            )
            print(asset.asset_name)

            # Send initial request
            print("Sending client request - soc.")
            client_request = api_pb2.VQLCollectorArgs(
                max_wait=1,
                Query=[
                    api_pb2.VQLRequest(
                        Name="ClientQuery",
                        VQL=client_query,
                    ),
                ],
            )

            for client_response in stub.Query(client_request):
                try:
                    client_results = json.loads(client_response.Response)
                    global client_id
                    client_id = client_results[0]["client_id"]
                    print(client_id)
                except Exception:
                    self.log.info({"message": "Could not find a suitable client."})
                    pass

            # Define initial query
            init_query = (
                'SELECT collect_client(client_id="'
                + client_id
                + '", artifacts=["Windows.Remediation.Quarantine"],'
                " spec=dict(`Windows.Remediation.Quarantine`=dict())) FROM scope()"
            )

            # Send initial request
            print("Sending initial request - soc")
            request = api_pb2.VQLCollectorArgs(
                max_wait=1,
                Query=[
                    api_pb2.VQLRequest(
                        Name="Query",
                        VQL=init_query,
                    ),
                ],
            )

            for response in stub.Query(request):
                try:
                    init_results = json.loads(response.Response)
                    flow = list(init_results[0].values())[0]
                    print("made it to loop")
                    flow_id = str(flow["flow_id"])
                    print(init_results)
                    # Define second query
                    flow_query = (
                        "SELECT * from flows(client_id='"
                        + str(flow["request"]["client_id"])
                        + "', flow_id='"
                        + flow_id
                        + "')"
                    )
                    print(flow_query)
                    state = "RUNNING"

                    # Check to see if the flow has completed
                    while state != "FINISHED":
                        followup_request = api_pb2.VQLCollectorArgs(
                            max_wait=10,
                            Query=[
                                api_pb2.VQLRequest(
                                    Name="QueryForFlow",
                                    VQL=flow_query,
                                ),
                            ],
                        )

                        for followup_response in stub.Query(followup_request):
                            try:
                                flow_results = json.loads(followup_response.Response)
                            except Exception:
                                pass
                        state = flow_results[0]["state"]
                        print(state)
                        global artifact_results
                        artifact_results = flow_results[0]["artifacts_with_results"]
                        self.log.info({"message": state})
                        time.sleep(1.0)
                        if state == "FINISHED":
                            asset.asset_tags = f"{asset.asset_tags},quarantined:yes"
                            time.sleep(5)
                            print(state)
                            break
                        if state == "ERROR":
                            asset.asset_tags = f"{asset.asset_tags},quarantined:yes"
                            time.sleep(5)
                            print(state)
                            break
                except Exception:
                    pass

        return InterfaceStatus.I2Success()

    def handle_linux(self, asset):
        """
        Handles an Asset and Quarantines the endpoint via Velociraptor
        :param asset: ASSET instance
        :return: IIStatus
        """

        self.log.info(f"Running Quarantine for {asset.asset_name}")

        creds = grpc.ssl_channel_credentials(
            root_certificates=self.config["ca_certificate"].encode("utf8"),
            private_key=self.config["client_private_key"].encode("utf8"),
            certificate_chain=self.config["client_cert"].encode("utf8"),
        )

        options = (("grpc.ssl_target_name_override", "VelociraptorServer"),)

        with grpc.secure_channel(
            self.config["api_connection_string"],
            creds,
            options,
        ) as channel:
            stub = api_pb2_grpc.APIStub(channel)

            client_query = (
                "select client_id from clients(search='host:" + asset.asset_name + "')"
            )
            print(asset.asset_name)

            # Send initial request
            print("Sending client request - soc.")
            client_request = api_pb2.VQLCollectorArgs(
                max_wait=1,
                Query=[
                    api_pb2.VQLRequest(
                        Name="ClientQuery",
                        VQL=client_query,
                    ),
                ],
            )

            for client_response in stub.Query(client_request):
                try:
                    client_results = json.loads(client_response.Response)
                    global client_id
                    client_id = client_results[0]["client_id"]
                    print(client_id)
                except Exception:
                    self.log.info({"message": "Could not find a suitable client."})
                    pass

            # Define initial query
            init_query = (
                'SELECT collect_client(client_id="'
                + client_id
                + '", artifacts=["Linux.Remediation.Quarantine"],'
                " spec=dict(`Linux.Remediation.Quarantine`=dict())) FROM scope()"
            )

            # Send initial request
            print("Sending initial request - soc")
            request = api_pb2.VQLCollectorArgs(
                max_wait=1,
                Query=[
                    api_pb2.VQLRequest(
                        Name="Query",
                        VQL=init_query,
                    ),
                ],
            )

            for response in stub.Query(request):
                try:
                    init_results = json.loads(response.Response)
                    flow = list(init_results[0].values())[0]
                    print("made it to loop")
                    flow_id = str(flow["flow_id"])
                    print(init_results)
                    # Define second query
                    flow_query = (
                        "SELECT * from flows(client_id='"
                        + str(flow["request"]["client_id"])
                        + "', flow_id='"
                        + flow_id
                        + "')"
                    )
                    print(flow_query)
                    state = "RUNNING"

                    # Check to see if the flow has completed
                    while state != "FINISHED":
                        followup_request = api_pb2.VQLCollectorArgs(
                            max_wait=10,
                            Query=[
                                api_pb2.VQLRequest(
                                    Name="QueryForFlow",
                                    VQL=flow_query,
                                ),
                            ],
                        )

                        for followup_response in stub.Query(followup_request):
                            try:
                                flow_results = json.loads(followup_response.Response)
                            except Exception:
                                pass
                        state = flow_results[0]["state"]
                        print(state)
                        global artifact_results
                        artifact_results = flow_results[0]["artifacts_with_results"]
                        self.log.info({"message": state})
                        time.sleep(1.0)
                        if state == "FINISHED":
                            asset.asset_tags = f"{asset.asset_tags},quarantined:yes"
                            time.sleep(5)
                            print(state)
                            break
                        if state == "ERROR":
                            asset.asset_tags = f"{asset.asset_tags},quarantined:yes"
                            time.sleep(5)
                            print(state)
                            break
                except Exception:
                    pass

        return InterfaceStatus.I2Success()
