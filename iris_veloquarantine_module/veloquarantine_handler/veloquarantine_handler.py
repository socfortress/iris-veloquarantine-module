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

import iris_interface.IrisInterfaceStatus as InterfaceStatus
from app.datamgmt.manage.manage_attribute_db import add_tab_attribute_field


class VeloquarantineHandler(object):
    def __init__(self, mod_config, server_config, logger):
        self.mod_config = mod_config
        self.server_config = server_config
        self.veloquarantine = self.get_veloquarantine_instance()
        self.log = logger

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

    def handle_domain(self, ioc):
        """
        Handles an IOC of type domain and adds VT insights

        :param ioc: IOC instance
        :return: IIStatus
        """

        self.log.info(f'Getting domain report for {ioc.ioc_value}')

        # TODO! do your stuff, then report it to the element (here an IOC)

        if self.mod_config.get('veloquarantine_report_as_attribute') is True:
            self.log.info('Adding new attribute veloquarantine Domain Report to IOC')

            report = ["<TODO> report from veloquarantine"]

            status = self.gen_domain_report_from_template(self.mod_config.get('veloquarantine_domain_report_template'), report)

            if not status.is_success():
                return status

            rendered_report = status.get_data()

            try:
                add_tab_attribute_field(ioc, tab_name='veloquarantine Report', field_name="HTML report", field_type="html",
                                        field_value=rendered_report)

            except Exception:

                self.log.error(traceback.format_exc())
                return InterfaceStatus.I2Error(traceback.format_exc())
        else:
            self.log.info('Skipped adding attribute report. Option disabled')

        return InterfaceStatus.I2Success()
