
import logging
logger = logging.getLogger(__name__)

from apstra.dao import VniPool, HttpStatus, ID
from apstra.errors import ErrorApstraAPI
from apstra.internal import Color
from apstra.resources import Range 
from dataclasses import asdict
from dacite import from_dict
from pprint import pprint
from typing import Dict, List, Optional, Tuple, Union

class ResourcesVniPool:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
        
    # #################################################################################################################
    # SET / CREATE
    #
    def create(self, name: str, ranges: list = []) -> Union[ID, ErrorApstraAPI]:
        color = Color()
        
        check_if_exist = self.get(name)
        if check_if_exist is not None and isinstance(check_if_exist, object):
            logger.info(f"VNI Pool: {color.get('YELLOW')}{name} -> Exist  {color.get('GREEN')}-> {check_if_exist}")
            return(1)
        
        context = {"display_name": name}
        if len(ranges)  > 0:
            new_range = Range()
            for r in ranges:
                rr = r.replace("to","-").replace(" ", "").split("-")
                first = int(rr[0])
                last = int(rr[1])
                if first <= 4095:
                    logger.warning(f"WARNING: Range start '{first}' - VNI must be between 4096 and 16777214 - will SKIP this range")
                    continue
                if last <= 4095:
                    logger.warning(f"WARNING: Range end '{last}' - VNI must be between 4096 and 16777214 - will SKIP this range")
                    continue
                if not first <= last:
                    logger.warning(f"WARNING: the beginning of the range must be smaller than or equal to the end of the range")
                    continue
                new_range.add_range(int(first),int(last))
            context['ranges'] = new_range.get_non_overlapping_ranges()
        
        logger.debug(f"VNI: JSON Context: {context}")
        json_to_sent = self.apstra.rest.generate_template('resource_vni_pool', context)
        aos_return = self.apstra.rest.post_json_response('/api/resources/vni-pools', data=json_to_sent)

        if aos_return.get('id'):
            r = ID()
            r.id = aos_return['id']

        return(r)
    
    # #################################################################################################################
    # GET
    # 
    def get(self, search_value = None, search_key: str = "display_name", bp_type: str = 'staging') -> Union[VniPool,None]:
        uri = f"/api/resources/vni-pools?type={bp_type}"
        try:
            reponse_data = self.apstra.rest.search_object(search_value, search_key, uri)
            if reponse_data is None:
                return None
        except:
            return None
        
        vni_pool = from_dict(data_class=VniPool, data=reponse_data)
        return(vni_pool)
    
    def get_by_id(self, pool_id: str) -> Union[VniPool,None]:
        reponse_data = self.apstra.rest.get_json_response(f"/api/resources/vni-pools/{pool_id}")
        vni_pool = from_dict(data_class=VniPool, data=reponse_data)
        return(vni_pool)

    def get_all(self) -> List[VniPool]:        
        uri = f"/api/resources/vni-pools"
        apstra_reponse = self.apstra.rest.get_json_response(uri)
        return_list = list()
        for data_item in apstra_reponse.get('items'):
            obj = from_dict(data_class=VniPool, data=data_item)
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
            
        reponse = self.apstra.rest.delete_request(f"/api/resources/vni-pools/{id}", params={"async": "full"})
        return HttpStatus(reponse.status_code)

