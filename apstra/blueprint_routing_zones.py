#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)
import json
import inspect

from pprint import pprint
from requests.utils import requote_uri
from typing import List, Tuple, Union, Dict, Optional
from dataclasses import asdict
from dacite import from_dict
from apstra.errors import ErrorApstraAPI
from apstra.dao import RoutingZone, AsyncResponse, HttpStatus

class RoutingZones:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, routing_zone: Union[RoutingZone, Dict]) -> Union[RoutingZone,ErrorApstraAPI]:
        if isinstance(routing_zone, RoutingZone):
            routing_zone = asdict(routing_zone)

        if routing_zone.get('routing_policie') is None:
            routing_zone['routing_policie_id'] = self.apstra.blueprint.routing_policies.get("Default_immutable").id
        else:
            routing_zone['routing_policie_id'] = self.apstra.blueprint.routing_policies.get(routing_zone['routing_policie']).id

        logger.debug(f"Routing-Zone Transformation: {routing_zone}")
        data_to_sent = self.apstra.rest.generate_template(template_name='routing-zone', context=routing_zone)
        logger.debug(f"Template JSON Data: {json.dumps(data_to_sent)}")
  
        try:
            uri = f"/api/blueprints/{self.parameters.active_bp.id}/security-zones"
            apstra_routing_zone = self.apstra.rest.post_json_response(uri, data=data_to_sent)
            routing_zone_id = apstra_routing_zone['id']
        except Exception as e:
            self_function = getattr(self, inspect.currentframe().f_code.co_name)
            logger.critical(f"EXCEPTION-> Apstra [{self.apstra.parameters.active_controller}] > Blueprint [{self.apstra.parameters.active_bp.label}] > {self.__class__.__name__} > {self_function.__name__}")
            logger.critical(f"Exception: {e}")
            raise ErrorApstraAPI(e)

        # RoutingZone leaf loopback pool
        routing_zone['leaf_loopback_ip_pools_ids'] = list()
        if routing_zone.get('leaf_loopback_ip_pools'):
            for pool_name in routing_zone['leaf_loopback_ip_pools']:
                if self.apstra.internal.validate_uuid4(pool_name) is not True:
                    aos_pool = self.apstra.resources.ipv4_pools.get(pool_name)
                    if isinstance(aos_pool, object):
                        logger.debug(f"RZ Transformation: Loopback IP Pool Name: {pool_name} -> ID: {aos_pool.id}")
                        routing_zone['leaf_loopback_ip_pools_ids'].append(aos_pool.id)
                else:
                    routing_zone['leaf_loopback_ip_pools_ids'].append(pool_name)

            # SZ leaf loopback pool
            group_path = requote_uri(f"sz:{routing_zone_id},leaf_loopback_ips")
            self.apstra.resources.apply_resource_groups(
                bp_id=self.parameters.active_bp.id,
                resource_type="ip",
                group_name=group_path,
                pool_ids=routing_zone['leaf_loopback_ip_pools_ids']
            )
            logger.debug(f"RZ: Applying 'leaf_loopback_ips' resource pool '{routing_zone['leaf_loopback_ip_pools_ids']}' to Routing Zone '{routing_zone['label']}' in blueprint '{self.parameters.active_bp.label}'")
        
        # DHCP servers (relay)
        if routing_zone.get('dhcp_servers'):
            self.put_routing_zone_dhcp(routing_zone_id, routing_zone['dhcp_servers'])
            logger.debug(f"RZ: Applying dhcp servers '{routing_zone['dhcp_servers']}' to SRouting Zone '{routing_zone['label']}' in blueprint '{self.parameters.active_bp.label}'")    
        
        
        rz = from_dict(data_class=RoutingZone, data=routing_zone) 
        return(rz)
    
    def put_routing_zone_dhcp(self, routing_zone_id: str, dhcp_servers: List):
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/security-zones/{routing_zone_id}/dhcp-servers"
        dhcp_servers = {"items": dhcp_servers}
        reponse = self.apstra.rest.put_json_response(uri, data=dhcp_servers)
        return reponse
 
    # #################################################################################################################
    # GET
    #  
    def get(self, search_value = None, search_key: str = "vrf_name", bp_type: str = 'staging') -> Union[RoutingZone,None]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/security-zones?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        routing_zone = from_dict(data_class=RoutingZone, data=reponse_data)
        return(routing_zone)

    def get_by_id(self, rz_id: str) -> Union[RoutingZone,None]:
        reponse_data = self.apstra.rest.get_json_response(f"/api/blueprints/{self.parameters.active_bp.id}/security-zones/{rz_id}")
        reponse = from_dict(data_class=RoutingZone, data=reponse_data)
        return(reponse)

    def get_nested(self, search_value = None, search_key: str = "vrf_name", bp_type: str = 'staging') -> Union[RoutingZone,None]:
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/security-zones?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        routing_zone = from_dict(data_class=RoutingZone, data=reponse_data)
        routing_zone.routing_policy = self.apstra.blueprint.routing_policies.get(routing_zone.routing_policy_id, search_key="id")
        return(routing_zone)

    def get_all(self) -> List[RoutingZone]:        
        uri = f"/api/blueprints/{self.parameters.active_bp.id}/security-zones"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('items').values():
            obj = from_dict(data_class=RoutingZone, data=data_item)
            return_list.append(obj)
        return(return_list)

    
    # #################################################################################################################
    # DELETE
    #  
    def delete(self, routing_zone: str) -> Union[HttpStatus,ErrorApstraAPI]:
        # We assume that provided 'routing_zone' is 'label' / not 'id'
        rz = self.get(routing_zone)
        if rz is None:
            # Not found name -> we assume that provided 'routing_zone' is 'id'
            routing_zone_id = routing_zone
        else:
            # Provided 'routing_zone' is a lable -> we get 'id'
            routing_zone_id = rz.id
            
        reponse = self.apstra.rest.delete_request(f"/api/blueprints/{self.parameters.active_bp.id}/security-zones/{routing_zone_id}", params={"async": "full"})
        return HttpStatus(reponse.status_code)
