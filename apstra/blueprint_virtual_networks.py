#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

import inspect

from pprint import pprint
from dacite import from_dict
from dataclasses import asdict
from typing import Union, Tuple, List, Dict
import json

from apstra.errors import ErrorApstraAPI
from apstra.dao import VirtualNetwork, BoundTo, HttpStatus

class VirtualNetworks:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, virtual_network:  Union[VirtualNetwork, Dict]) -> Union[VirtualNetwork,ErrorApstraAPI]:
        if isinstance(virtual_network, VirtualNetwork):
            virtual_network = asdict(virtual_network)
        
        bp_id = self.apstra.parameters.active_bp.id
        
        if virtual_network.get('routing_zone'):
            rz = self.apstra.blueprint.routing_zones.get(virtual_network['routing_zone'])
            try:
                virtual_network['security_zone_id'] = rz.id
            except:
                logger.critical("Blueprint Virtual Networks > create_virtual_network")
                raise ErrorApstraAPI(f"Not able to find Routing-Zone {virtual_network['routing_zone']} ID ")
            logger.debug(f"RZ: {virtual_network['routing_zone']}: {rz.id}")
        
        #del(virtual_network['routing_zone'])

        virtual_network['vn_id'] = str(virtual_network['vn_id'])

        # Check if redundancy-group paire switches is included in bound_to
        for i, bound in enumerate(virtual_network['bound_to']):
            # Lets check first if defined switch is/exist in this Blueprint
            # if not / SKIP this bound
            bound_system_name = bound.get("system")
            apstra_db = self.parameters.systems[bp_id].get(bound_system_name)
            if apstra_db is None:
                logger.info(f"VN: {virtual_network['label']}: system: {bound_system_name} in 'bound_to' not found in blueprint {bp_id} - SKIP")
                del(virtual_network['bound_to'][i])
                continue

            #pprint(apstra_db)
            if apstra_db['type'] != "rg" and apstra_db['hostname'] != apstra_db['label'] and apstra_db['hostname'] == bound['system']:
                logger.warning(f"VN: {virtual_network['label']}: system: {bound_system_name} is a hostname - replaced by label:  {apstra_db['label']}")
                bound['system'] = apstra_db['label']
                
            # If bound['system'] is switch and this switch is part of 'redundancy_group'
            # we need to add all nodes of this 'redundancy_group'
            if apstra_db['type'] == 'switch':
                if apstra_db.get('rg'):
                    rg_label = apstra_db['rg']['label']
                    rg = self.parameters.systems[bp_id][rg_label]
                    rg_all_systems = rg['systems']['label']
                    for item in rg_all_systems:
                        found = False
                        for d in virtual_network['bound_to']:
                            if d['system'] == item:
                                found = True
                                break
                        if not found:
                            logger.info(f"VN: {virtual_network['label']}: bound_to added {item}")
                            virtual_network['bound_to'].append({'system': item })

        # Transform bound['system'] -> bound['system_id']
        for bound in virtual_network['bound_to']:
            system_name = bound.get("system")
            bound['system_id'] = self.parameters.systems[bp_id][system_name]['id']
            if bound.get('vlan_id') and virtual_network.get('vlan_id'):
                logger.info(f"VN: {virtual_network['label']}: bound_to={bound['system']}\\vlan_id={bound['vlan_id']} -> vlan_id overwriten by: {virtual_network['vlan_id']}")
                bound['vlan_id'] = virtual_network['vlan_id']
            #del(bound['system'])

        # Transform bound['access_switches'] -> bound['access_switch_node_ids']
        for bound in virtual_network['bound_to']:
            # Check if there is defined 'access_switche'
            if bound.get('access_switches'):
                bound['access_switch_node_ids'] = list()
                for acc_swi_system_name in bound['access_switches']:
                    try:
                        # Try to get Access Switch ID based on NAME - from acc_swi_system_name 
                        apstra_db = self.parameters.systems[bp_id][acc_swi_system_name]
                        apstra_db_id = apstra_db['id']
                    except:
                        logger.critical(f"VN: {virtual_network['label']}: bound_to_access_switches={apstra_db_id} failed / not able to get ID for this switch")
                        raise ErrorApstraAPI(f"bound_to_access_switches={apstra_db_id} failed / not able to get ID for this switch", 404)

                    if apstra_db['type'] != "rg" and  apstra_db['hostname'] != apstra_db['label'] and apstra_db['hostname'] == acc_swi_system_name:
                        logger.warning(f"VN: {virtual_network['label']}: access switch: {acc_swi_system_name} is a hostname - please change this to:  {apstra_db['label']}") 
                    
                    bound['access_switch_node_ids'].append(apstra_db_id)
                    
 
                del(bound['access_switches'])
        
        logger.debug(f"VN Transformation: {virtual_network}")
        json_to_sent = self.apstra.rest.generate_template('virtual-network', virtual_network)
        logger.debug(f"JSON: {json_to_sent}")
        
        try:
            uri = f"/api/blueprints/{bp_id}/virtual-networks"
            apstra_reponse = self.apstra.rest.post_json_response(uri,data=json_to_sent)
        except Exception as e:            
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"ERROR: data={json.dumps(json_to_sent, indent=4)}")
            logger.critical(f"Exception: {e}")
            raise ErrorApstraAPI(e)

        return(apstra_reponse)
    


    # #################################################################################################################
    # GET
    # 
    def get(self, search_value = None, search_key: str = "label", bp_type: str = 'staging', vni_id_search: bool = False) -> Union[VirtualNetwork,None]:
        # If vni_id_search=True -> you can use define vni as ie. VNI232334 / or simple id 232334
        if vni_id_search is True:
            if isinstance(search_value, int) or (isinstance(search_value, str) and search_value.lower().startswith('vni')):
                search_value = str(search_value).replace("VNI", "")
                search_key = 'vn_id'
        
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/virtual-networks?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        virtual_network = from_dict(data_class=VirtualNetwork, data=reponse_data)
        return(virtual_network)

    def get_by_id(self, vn_id: str) -> Union[VirtualNetwork,None]:
        reponse_data = self.apstra.rest.get_json_response(f"/api/blueprints/{self.parameters.active_bp.id}/virtual-networks/{vn_id}")
        reponse = from_dict(data_class=VirtualNetwork, data=reponse_data)
        return(reponse)

    def get_all(self) -> List[VirtualNetwork]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/virtual-networks"        
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('virtual_networks').values():
            obj = from_dict(data_class=VirtualNetwork, data=data_item)
            return_list.append(obj)
        return(return_list)

    # #################################################################################################################
    # DELETE
    #  
    def delete(self, virtual_network: str) -> Union[HttpStatus,ErrorApstraAPI]:
        # We assume that provided 'virtual_network' is 'label' / not 'id'
        vn = self.get(virtual_network)
        if vn is None:
            # Not found name -> we assume that provided 'virtual_network' is 'id'
            virtual_network_id = virtual_network
        else:
            # Provided 'virtual_network' is a lable -> we get 'id'
            virtual_network_id = vn.id
            
        reponse = self.apstra.rest.delete_request(f"/api/blueprints/{self.parameters.active_bp.id}/virtual-networks/{virtual_network_id}", params={"async": "full"})
        return HttpStatus(reponse.status_code)