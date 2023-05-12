import logging
logger = logging.getLogger(__name__)

import requests
import os
import jinja2
import json

from apstra.errors import ErrorApstraAPI
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple, Union, Dict
from pprint import pprint
from collections import namedtuple

import apstra.dao

class Rest:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.parameters = main_class.parameters
        self.handlers = main_class.handlers
        self.default_headers = {"Content-Type": "application/json", "Accept": "application/json" }
        self.apstra = main_class
        self.controller = main_class.controller
        
    @property
    def url(self):
        return f"{self.controller.protocol}://{self.controller.host}:{self.controller.port}"

    def raw_request(self, method, uri, params, data, headers=None):
        if headers is None:
                headers = self.default_headers.copy()
                
        if self.controller.token is not None:
            headers["AuthToken"] = self.controller.token
            
        response = None
        try:
            uri = f"{self.url}/{uri.lstrip('/')}"
            #print(uri)
            response = self.controller.session.request(
                method,
                uri,
                params=params,
                json=data,
                headers=headers,
                verify=self.controller.ssl_validation, 
                timeout=self.controller.timeout
            )

        except requests.RequestException as e:
            raise ErrorApstraAPI(message=str(e))
        finally:
            logger.debug(f"AosRawRequest: {method} {uri} params={params} json={self.apstra.internal.redacted(data)} headers={self.apstra.internal.redacted(headers)}; response={response}" )
 
        if response.status_code == 401:
            raise ErrorApstraAPI(message="Authentication failed", code=response.status_code)
        elif response.status_code >= 400:
            raise ErrorApstraAPI(message=response.text, code=response.status_code)

        return response

    def raw_request_json(self, method, uri, params, data, headers=None):
        resp = self.raw_request(method, uri, params, data, headers)

        try:
            if method == "GET" and resp.status_code == 404:
                return None
            if method == "PUT" and resp.status_code == 204:
                return None
            if resp.ok:
                return resp.json()
        except (TypeError, ValueError) as e:
            msg = (f"JSON deserialization failed for '{method} {uri} params={params} data={data}'. Error {type(e)}: {e}")
            logger.critical(msg)
            raise ErrorApstraAPI(msg) from e

    def try_raw_request_json(self, method, uri, params, data, headers):
        try:
            return self.raw_request_json(method, uri, params, data, headers)
        except ErrorApstraAPI:
            pass

    def get_json_response(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request_json("GET", uri, params, data, headers)
    
    def post_json_response(self, uri: str, params=None, data=None, headers=None):
        if params is None:
            return self.raw_request_json("POST", uri, params, data, headers)
        
        if params.get('async') == 'full':
            task_id = self.raw_request_json("POST", uri, params, data, headers)['task_id']
            my_lambda = lambda: self.apstra.tasks.is_task_active(task_id) is False
            self.apstra.tasks.check_until_true(my_lambda, 60)
            task_info = self.apstra.tasks.get_task_by_id(task_id)
            if task_info['status'] != "succeeded":
                raise ErrorApstraAPI(f"Task: {task_id} - has status: {task_info['status']} - details: {task_info['detailed_status']}")
            else:
                r = task_info['detailed_status'].get('api_response')
                r['task_id'] = task_id
                r['task_status'] = "succeeded"
                begin_time = datetime.fromisoformat(task_info['begin_at'][:-5]) 
                last_updated_time = datetime.fromisoformat(task_info['last_updated_at'][:-5])
                delta_time = (last_updated_time - begin_time).total_seconds()
                r['task_processing_time'] = delta_time
                return r
        
    def patch_json_response(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request_json("PATCH", uri, params, data, headers)

    def put_json_response(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request_json("PUT", uri, params, data, headers)

    def delete_json_response(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request_json("DELETE", uri, params, data, headers)
    
    def get(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request("GET", uri, params, data, headers)

    def put_request(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request("PUT", uri, params, data, headers)

    def patch_request(self, uri: str, params=None, data=None, headers=None):
        return self.raw_request("PATCH", uri, params, data, headers)

    def delete_request(self, uri, params=None, data=None, headers=None):
        return self.raw_request("DELETE", uri, params, data, headers)

    def get_resource(self,url):
        api_resource = "api_"+url.split("/api/",2)[1].replace("/","_")
        # Remember to keek _name - as variable name can become same as method name
        setattr(self, str({api_resource}), None)
        r = self.http_get_request(url)
        if r.get('items'):
            setattr(self, str({api_resource}), r['items'])
            return(r['items'])
        elif 'items' in r.keys():
            setattr(self, str({api_resource}), list())
            return(list())
        elif isinstance(r, dict):
            setattr(self, str({api_resource}), r)
            return(r)
        else:
            ErrorApstraAPI(HTTPStatus.FAILED_DEPENDENCY, f"Apstra Controller didnt return {api_resource} list", status="fail") 
            


    def generate_template(self, template_name = None, context = dict()):
        current_path = os.path.dirname(os.path.abspath(__file__))
        templateLoader = jinja2.FileSystemLoader(searchpath=f"{current_path}/../templates/")
        templateEnv = jinja2.Environment(loader=templateLoader)
        try:
            template = templateEnv.get_template(f"{template_name}.jinja")
            ct_data = template.render(context)
        except Exception as e:
            logger.critical(f'Not able to generate json {current_path}/../templates/{template_name}.jinja')
            logger.critical(e)
            ErrorApstraAPI(e)
        return(json.loads(ct_data))

    def login(self, apstra_server_name): 
        logger.debug(f"Login controller details: {self.controller}")
        response = self.post_json_response("/api/aaa/login", data={"username": self.controller.username, "password": self.controller.password})
        
        self.controller.token = response.get("token")
        self.controller.user_uuid = response.get("id")
        return {"token": self.controller.token, "user_uuid": self.controller.user_uuid}
    
    
    
    
    
    def search(self, value = str, key = "label", uri=None) -> List[Tuple]:
        if uri is None:
            return[]
        data = self.apstra.rest.get_json_response(uri)
        filtered = self.find_by(data, key, value)
        return (filtered)

    def search_object(self, value = str, key = "label", uri=None) -> Tuple|None:
        if uri is None:
            return[]
        data = self.apstra.rest.get_json_response(uri)
        filtered = self.find_by(data, key, value)
        
        if len(filtered) == 1:
            return filtered[0]
        else:
            if len(filtered) > 1:
                logger.critical(f'search_object -> expected to find one item - unfortunately found {len(filtered)}')
                ErrorApstraAPI()
            else:
                return None

    def find_by(self, data: Union[List[dict], dict], variable_name='label', value=None) -> List[Dict]:
        #pprint(data)
        if isinstance(data, dict):
            k = ''
            keys_to_process = ['nodes', 'items', 'virtual_networks', 'policies']
            for key in keys_to_process:
                if key in data:
                    k = key
                    try:
                        if isinstance(data[key], list):
                            items_list = data[key]
                        items_list = list(data[key].values())
                    except:
                        continue
                    del(data)
                    data = items_list
                    continue
        
        #pprint(data)
        results = []
        for item in data[k] if isinstance(data, dict) else data:
            if item.get(variable_name) == value:
                results.append(item)

        return results
    
    
    def qe_query(self, query: str, params: dict = None, bp_id: str = None) -> List:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        uri = f"/api/blueprints/{bp_id}/qe"
        data = {"query": query}
        resp = self.post_json_response(uri, data=data, params=params)
        return resp["items"]