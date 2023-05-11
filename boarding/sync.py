#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

from pprint import pprint


RED = '\033[1;31m'
GREEN = '\033[1;32m'
GREEN0 = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
RESET = '\033[0m'

class Sync():
    from . import BoardingAOS
    
    from apstra.dao import RoutePolicy
    
    def __init__(self, main_class: BoardingAOS):
        self.parameters = main_class.parameters
        self.internal = main_class.internal
        self.apstra = main_class.apstra
        
    ##################################################
    ## SYNC
    def run(self):
        logger.info(self.internal.generate_line(150))
        logger.info(f"START: Sync")
        logger.info(self.internal.generate_line(150))
        for bp_name,bp_parameters in self.parameters.config['blueprints'].items():
            apstra_server_name = bp_parameters['apstra']

            self.apstra.client.connect(apstra_server_name)
            self.apstra.client.change_blueprint(bp_name)

            if bp_parameters.get('sync'):
                self.sync_status = bp_parameters['sync']
                if bp_parameters['sync'] == True:
                    self.sync_status = f"{GREEN}ON{GREEN0}"
            else:
                self.sync_status = f"{YELLOW}OFF{GREEN0}"
            logger.info(f"SYNC: BP: {bp_name} - status: {self.sync_status}")

            logger.info(self.internal.generate_line(97,3))
            
            self.routing_policies()
            self.nodes()
            self.connectivity_template()
            self.virtual_network()
            self.routing_zones()
            


    def routing_policies(self):
        routing_policies_list = self.apstra.blueprint.routing_policies.get_all()
        logger.info(f"SYNC: Routing Policy ({self.parameters.active_bp.label})")
        for apstra_graph_routing_policie in routing_policies_list:
            sync_element = dict()
            sync_element['apstra_graph'] = apstra_graph_routing_policie

            try:
                config_element = list(self.internal.dsearch(self.parameters.config['blueprints'][self.parameters.active_bp.label]['routing-policies'], label=apstra_graph_routing_policie.label))
                config_element_name = config_element[0].get('label')
                sync_element['yaml'] = config_element[0]
                sync_element['status'] = "OK"
                print_status = "OK"
            except:
                config_element_name = 'Not Exist'
                print_status = f"{RED}NOK (need to be removed from Apstra Server){RESET}"
                sync_element['status'] = "DELETE"

            if "OFF" in self.sync_status and sync_element['status'] != "OK":
                sync_element['status'] = "OK"
                print_status = f"OK [sync: OFF]"
                
            self.parameters.sync[self.parameters.active_bp.label]['nodes'][apstra_graph_routing_policie.label] = sync_element
    
            if print_status.startswith("OK"):
                logger.info(f"        {apstra_graph_routing_policie.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            else:
                logger.warning(f"        {apstra_graph_routing_policie.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            
        logger.debug("SYNC: self.parameters.sync[bp_name]['routing-policies'][config_element_name]")
        logger.info(self.internal.generate_line(150))
        return(0)    

    def nodes(self):
        nodes_list = self.apstra.blueprint.nodes.get_all_servers(self.parameters.active_bp.id)
        logger.info(f"SYNC: Node ({self.parameters.active_bp.label})")
        for apstra_graph_node in nodes_list:
            sync_element = dict()
            sync_element['apstra_graph'] = apstra_graph_node._asdict()

            try:
                config_element = list(self.internal.dsearch(self.parameters.config['blueprints'][self.parameters.active_bp.label]['nodes'], label=apstra_graph_node.label))
                config_element_name = config_element[0].get('label')
                sync_element['yaml'] = config_element[0]
                sync_element['status'] = "OK"
                print_status = "OK"
            except:
                config_element_name = 'Not Exist'
                print_status = f"{RED}NOK (need to be removed from Apstra Server){RESET}"
                sync_element['status'] = "DELETE"

            if "OFF" in self.sync_status and sync_element['status'] != "OK":
                sync_element['status'] = "OK"
                print_status = f"OK [sync: OFF]"

            if apstra_graph_node.tags is not None and 'protect' in apstra_graph_node.tags:
                sync_element['status'] = "OK"
                print_status = "OK [tag: protected]"
                
            self.parameters.sync[self.parameters.active_bp.label]['nodes'][apstra_graph_node.label] = sync_element
    
            if print_status.startswith("OK"):
                logger.info(f"        {apstra_graph_node.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            else:
                logger.warning(f"        {apstra_graph_node.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            
        logger.debug("SYNC: self.parameters.sync[bp_name]['nodes'][config_element_name]")
        logger.info(self.internal.generate_line(150))
        return(0)     


    def routing_zones(self):
        rz_list = self.apstra.blueprint.routing_zones.get_all()
        logger.info(f"SYNC: RZ ({self.parameters.active_bp.label})")
        for apstra_graph_rz in rz_list:
            sync_element = dict()
            sync_element['apstra_graph'] = apstra_graph_rz
            
            try:
                config_element = list(self.internal.dsearch(self.parameters.config['blueprints'][self.parameters.active_bp.label]['routing-zones'], label=apstra_graph_rz.vrf_name))
                config_element_name = config_element[0].get('label')
                sync_element['yaml'] = config_element[0]
                sync_element['status'] = "OK"
                print_status = "OK"
            except:
                config_element_name = 'Not Exist'
                print_status = f"{RED}NOK (need to be removed from Apstra Server){RESET}"
                sync_element['status'] = "DELETE"

            if "OFF" in self.sync_status and sync_element['status'] != "OK":
                sync_element['status'] = "OK"
                print_status = f"OK [sync: OFF]"
                
            if apstra_graph_rz.vrf_name == "default":
                print_status = "OK  (default)"
                sync_element['status'] = "OK"

            self.parameters.sync[self.parameters.active_bp.label]['routing-zones'][apstra_graph_rz.vrf_name] = sync_element
            
            if print_status.startswith("OK"):
                logger.info(f"        {apstra_graph_rz.vrf_name.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            else:
                logger.warning(f"        {apstra_graph_rz.vrf_name.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
        
        logger.debug("SYNC: self.parameters.sync[bp_name]['routing-zones'][config_element_name]")
        logger.info(self.internal.generate_line(150))
        return(0)
    
    def virtual_network(self):        
        vn_list = self.apstra.blueprint.virtual_networks.get_all()

        logger.info(f"SYNC: VN ({self.parameters.active_bp.label})")
        for apstra_graph_vn in vn_list:
            sync_element = dict()
            sync_element['apstra_graph'] = apstra_graph_vn

            try:
                config_element = list(self.internal.dsearch(self.parameters.config['blueprints'][self.parameters.active_bp.label]['virtual-networks'], label=apstra_graph_vn.label))
                config_element_name = config_element[0].get('label')
                sync_element['yaml'] = config_element[0]
                sync_element['status'] = "OK"
                print_status = "OK"
            except:
                config_element_name = 'Not Exist'
                print_status = f"{RED}NOK (need to be removed from Apstra Server){RESET}"
                sync_element['status'] = "DELETE"

            if "OFF" in self.sync_status and sync_element['status'] != "OK":
                sync_element['status'] = "OK"
                print_status = f"OK [sync: OFF]"

            self.parameters.sync[self.parameters.active_bp.label]['virtual-networks'][apstra_graph_vn.label] = sync_element

            if print_status.startswith("OK"):
                logger.info(f"        {apstra_graph_vn.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            else:
                logger.warning(f"        {apstra_graph_vn.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")

        logger.debug("SYNC: self.parameters.sync[bp_name]['virtual-networks'][config_element_name]")
        logger.info(self.internal.generate_line(150))
        return(0)
      
    def connectivity_template(self):
        ct_list = self.apstra.blueprint.connectivity_templates.get_all()

        logger.info(f"SYNC: CT ({self.parameters.active_bp.label})")
        for apstra_graph_ct in ct_list:
            if apstra_graph_ct.visible == False:
                continue 
            sync_element = dict()
            sync_element['apstra_graph'] = apstra_graph_ct
            
            try:
                config_element = list(self.internal.dsearch(self.parameters.config['blueprints'][self.parameters.active_bp.label]['connectivity-templates'], label=apstra_graph_ct.label))
                config_element_name = config_element[0].get('label')
                sync_element['yaml'] = config_element[0]
                sync_element['status'] = "OK"
                print_status = "OK"
            except:
                config_element_name = 'Not Exist'
                print_status = f"{RED}NOK (need to be removed from Apstra Server){RESET}"
                sync_element['status'] = "DELETE"
            
            if "OFF" in self.sync_status and sync_element['status'] != "OK":
                sync_element['status'] = "OK"
                print_status = f"OK [sync: OFF]"
                
            if apstra_graph_ct.tags is not None and 'protect' in apstra_graph_ct.tags:
                sync_element['status'] = "OK"
                print_status = "OK [tag: protected]"
            
            self.parameters.sync[self.parameters.active_bp.label]['connectivity-templates'][apstra_graph_ct.label] = sync_element
            
            if print_status.startswith("OK"):
                logger.info(f"        {apstra_graph_ct.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
            else:
                logger.warning(f"        {apstra_graph_ct.label.rjust(40)} {BLUE}<AOS -vs- YAML>{GREEN0} {config_element_name.ljust(40)} --- status: {print_status}")
     
        logger.debug("SYNC: self.parameters.sync[bp_name]['connectivity-templates'][config_element_name]")
        logger.info(self.internal.generate_line(150))
        return(0)
    
    
