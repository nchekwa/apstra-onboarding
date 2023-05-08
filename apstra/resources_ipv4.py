
import logging
logger = logging.getLogger(__name__)

import ipaddress

from pprint import pprint
from typing import List, Tuple, Union, Dict, Optional
from dataclasses import asdict
from dacite import from_dict

from apstra.errors import ErrorApstraAPI
from apstra.internal import Color
from apstra.dao import IPv4Pool, HttpStatus, ID

class ResourcesIPv4Pool:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, name: str, subnets: list = []) -> Union[ID, ErrorApstraAPI]:
        color = Color()
                
        check_if_exist = self.get(name)
        if check_if_exist is not None and isinstance(check_if_exist, object):
            logger.info(f"IPv4 Pool: {color.get('YELLOW')}{name} -> Exist {color.get('GREEN')}-> {check_if_exist}")
            raise ErrorApstraAPI(f"ERROR - IPv4 Pool {name} exist - not able create new with same name")
        
        context = {"display_name": name}
        new_subnets = list()
        if len(subnets)  > 0:
            for s in subnets:
                try:
                    subnet_check = ipaddress.IPv4Network(s)
                except:
                    logger.warning(f"WARNING: subnet {s} dosnt look to be valid IPv4Network")
                    continue

                if subnet_check.is_private or subnet_check.is_global:
                    new_subnets.append({"network": s})
                else:
                    logger.warning(f"WARNING: subnet {s} dosnt look to be valid IPv4Network")
        context['subnets'] = new_subnets
        
        logger.debug(f"JSON Context: {context}")
        json_to_sent = self.apstra.rest.generate_template('resource_ipv4_pool', context)
        aos_return = self.apstra.rest.post_json_response('/api/resources/ip-pools', data=json_to_sent)
        
        if aos_return.get('id'):
            r = ID()
            r.id = aos_return['id']

        return(r)
    
    # #################################################################################################################
    # GET
    #  
    def get(self, search_value: str, search_key: str = "display_name", bp_type: str = 'staging') -> Union[IPv4Pool, None]: 
        uri = "/api/resources/ip-pools?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        ipv4_pool = from_dict(data_class=IPv4Pool, data=reponse_data)
        return(ipv4_pool)

    def get_by_id(self, pool_id: str) -> Union[IPv4Pool,None]:
        reponse_data = self.apstra.rest.get_json_response(f"/api/resources/ip-pools/{pool_id}")
        ipv4_pool = from_dict(data_class=IPv4Pool, data=reponse_data)
        return(ipv4_pool)

    def get_all(self) -> List[IPv4Pool]:        
        uri = "/api/resources/ip-pools"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('items'):
            obj = from_dict(data_class=IPv4Pool, data=data_item)
            return_list.append(obj)
        return(return_list)

    # #################################################################################################################
    # DELETE
    #  
    def delete(self, pool_name_or_id: str) -> Union[HttpStatus,ErrorApstraAPI]:
        response= self.get(pool_name_or_id)

        if response is None:
            id = pool_name_or_id
        else:
            id = response.id

        reponse = self.apstra.rest.delete_request(f"/api/resources/ip-pools/{id}", params={"async": "full"})
        return HttpStatus(reponse.status_code)