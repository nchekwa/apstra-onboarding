#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)
import inspect

import json
from pprint import pprint
from copy import deepcopy
from collections import namedtuple
from typing import List, Tuple, Dict, Union

from apstra.errors import ErrorApstraAPI

from apstra.dao import ObjPolicy
from dacite import from_dict
from dataclasses import asdict

from apstra.dao import VirtualNetwork, HttpStatus

class ConnectivityTemplates:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
    

    # #################################################################################################################
    # GET
    #  
    def get(self, search_value = None, search_key: str = "label", bp_type: str = 'staging') -> Union[ObjPolicy,None]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/obj-policy-export?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        routing_instance = from_dict(data_class=ObjPolicy, data=reponse_data)
        return(routing_instance)

    def get_all(self) -> List[ObjPolicy]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/obj-policy-export"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('policies'):
            obj = from_dict(data_class=ObjPolicy, data=data_item)
            return_list.append(obj)
        return(return_list)
    
    # #################################################################################################################
    # SET
    #  
    def create(self, ct_data):
        bp_id = self.parameters.active_bp.id
        
        check_name = self.get(ct_data.get('name'))
        if check_name is not None:
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"ERROR: data={json.dumps(ct_data, indent=4)}")
            raise ErrorApstraAPI(f"CT with name {ct_data.get('name')} allready exist")
        
        # Preapere template context
        ct_data['untagged_vn_node_id'] = str()
        ct_data['tagged_vn_node_ids'] = list()
        if ct_data.get('tags') is None:
            ct_data['tags'] = list()
            
        
        # untagged_vn
        if ct_data.get('untagged_vn'):
            if isinstance(ct_data['untagged_vn'], str):
                try:
                    apstra_graph_vn:VirtualNetwork = self.apstra.blueprint.virtual_networks.get(ct_data['untagged_vn'], vni_id_search=True)
                    ct_data['untagged_vn_node_id'] = apstra_graph_vn.id
                    ct_data['tags'].append(f"VNI{apstra_graph_vn.vn_id}")
                except:
                    logger.warning(f"CT: '{ct_data['label']}': missing untagged_vn: {ct_data['untagged_vn']} - SKIP virtual-network")
                    pass
            if isinstance(ct_data['untagged_vn'], list):
                try:
                    apstra_graph_vn:VirtualNetwork = self.apstra.blueprint.virtual_networks.get(ct_data['untagged_vn'][0], vni_id_search=True)
                    ct_data['untagged_vn_node_id'] = apstra_graph_vn.id
                    ct_data['tags'].append(f"VNI{apstra_graph_vn.vn_id}")
                except:
                    logger.warning(f"CT: '{ct_data['label']}': missing untagged_vn: {ct_data['untagged_vn']} - SKIP virtual-network")
                    pass
            del(ct_data['untagged_vn'])
        
        # tagged_vn
        if ct_data.get('tagged_vn') and ct_data.get('tagged_vns') is None:
            ct_data['tagged_vns'] = deepcopy(ct_data['tagged_vn'])
            del(ct_data['tagged_vn'])
        if ct_data.get('tagged_vns'):
            if isinstance(ct_data['tagged_vns'], str):
                try:
                    apstra_graph_vn:VirtualNetwork = self.apstra.blueprint.virtual_networks.get(ct_data['tagged_vns'], vni_id_search=True)
                    ct_data['tagged_vn_node_ids'].append(apstra_graph_vn.id)
                    ct_data['tags'].append(f"VNI{apstra_graph_vn.vn_id}")
                except:
                    logger.warning(f"CT: '{ct_data['label']}': missing tagged_vn: {ct_data['tagged_vns']} - SKIP virtual-network")
                    pass
            if isinstance(ct_data['tagged_vns'], list):   
                for tagged_vn in ct_data['tagged_vns']:
                    try:
                        apstra_graph_vn:VirtualNetwork = self.apstra.blueprint.virtual_networks.get(tagged_vn, vni_id_search=True)
                        ct_data['tagged_vn_node_ids'].append(apstra_graph_vn.id)
                        ct_data['tags'].append(f"VNI{apstra_graph_vn.vn_id}")
                    except:
                        logger.warning(f"CT: '{ct_data['label']}': missing tagged_vn: {tagged_vn} - SKIP virtual-network")
                        continue
            del(ct_data['tagged_vns'])
                        
        # Generate JSON Template based on ct_data
        ct_template = f"ct-{ct_data['template']}"
        json_to_sent = self.apstra.rest.generate_template(ct_template, ct_data)
        logger.debug(f"JSON: {json_to_sent}")
        logger.debug(f"CT Transformation: {ct_data}")

        try:
            uri = f"/api/blueprints/{bp_id}/obj-policy-import"
            apstra_reponse = self.apstra.rest.put_json_response(uri, data=json_to_sent)
        except Exception as e:
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"ERROR: data={json.dumps(json_to_sent, indent=4)}")
            logger.critical(f"Exception: {e}")
            raise ErrorApstraAPI(e)
        return(apstra_reponse)
    
    def assigne_connectivity_template(self, ct_name, switch_interface_id):
        bp_id = self.parameters.active_bp.id
        ct = self.get(ct_name)
        if ct is None:
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"ERROR: not able to assign template {ct_name}")
            logger.critical(f"Exception: {e}")
            raise ErrorApstraAPI(e, 404)
        else:
            #ct:ObjPolicy = self.get(ct_name)
            ct_id = ct.id
            
        #pprint(ct)
        data_to_patch = dict()
        data_to_patch['application_points'] = list()
        if_assign = dict()
        if_assign['id'] = switch_interface_id
        if_assign['policies'] = list()
        if_assign['policies'].append({"policy": ct_id, "used": True})
        data_to_patch['application_points'].append(if_assign)

        logger.debug(f"JSON Data: {data_to_patch}")
        #pprint(data_to_patch)
        try:
            uri = f"api/blueprints/{bp_id}/obj-policy-batch-apply"
            apstra_reponse = self.apstra.rest.patch_request(uri, data=data_to_patch, params={"async": "full"})
        except Exception as e:
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"ERROR: Problem with assign CT: {ct_name} -> data_to_patch: {json.dumps(data_to_patch, indent=4)}")
            logger.critical(f"Exception: {e}")
            raise ErrorApstraAPI(e, 500)
        return(apstra_reponse)
    
    
    # #################################################################################################################
    # DELETE
    #
    def delete(self, connectivity_templates: str) -> Union[HttpStatus,ErrorApstraAPI]:
        ct = self.get(connectivity_templates)

        if ct is None:
            connectivity_templates_id = connectivity_templates
        else:
            connectivity_templates_id = ct.id
        print(f"/api/blueprints/{self.parameters.active_bp.id}/endpoint-policies/{connectivity_templates_id}?delete_recursive=true")
        reponse = self.apstra.rest.delete_request(f"/api/blueprints/{self.parameters.active_bp.id}/endpoint-policies/{connectivity_templates_id}?delete_recursive=true")
        return HttpStatus(reponse.status_code)


