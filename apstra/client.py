#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from typing import List, Tuple, Union
from collections import namedtuple
from pprint import pprint
from time import sleep
from requests.utils import requote_uri
from dataclasses import dataclass, asdict
from apstra.errors import ErrorApstraAPI
import copy
from apstra.dao import ActiveBlueprint

class Client:
    from . import Apstra
    
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters
        self.handlers = main_class.handlers
        self.controller = main_class.controller

    #-------------------------------------------------------------------------------------------
    def add_aos_controller(self, *args, **kwargs):        
        if self.parameters.config.get('aos') is None:
            self.parameters.config['aos'] = dict()
            
        apstra_server_name = kwargs.get("name")
        if apstra_server_name:
            self.parameters.config["aos"][apstra_server_name] = dict()
            del(kwargs['name'])

        for key, value in kwargs.items():
            self.parameters.config['aos'][apstra_server_name][key] = value
    
        return(self.parameters.config['aos'][apstra_server_name])
    
    
    def connect(self, apstra_server_name):
        self.parameters.active_controller  = apstra_server_name
        if self.controller.name == apstra_server_name and self.controller.token is not None:
            # We are login on correct controller
            return(self.controller)
        
        if self.controller.name != apstra_server_name:
            # Request to change controller
            if self.handlers.apstra.get(apstra_server_name):
                if  self.handlers.apstra.get(apstra_server_name).token is not None:
                    logger.info(f"APSTRA: Reconnect to Controller {apstra_server_name}")
                    self.session(apstra_server_name)
                    return(self.controller)
            
            # Check if config exist for this name
            if not self.parameters.config['aos'].get(apstra_server_name):
                logger.error(f'Not found configuration for controller with name {apstra_server_name}')
                exit(1)
                
            if not self.handlers.apstra.get(apstra_server_name):
                from . import Controller
                self.handlers.apstra[apstra_server_name] = Controller()
                setattr(self.handlers.apstra[apstra_server_name], 'name', apstra_server_name)
                for key, value in self.parameters.config['aos'][apstra_server_name].items():
                    setattr(self.handlers.apstra[apstra_server_name], key, value)
                
        # Copy data from handler to self.controller
        self.apstra.internal.copy_dataclass(self.handlers.apstra[apstra_server_name], self.controller)

        logger.info(f"APSTRA: Connecting to '{apstra_server_name}'")
        try:
            login = self.apstra.rest.login(apstra_server_name)
        except Exception as e:
            logger.critical(f"EXIT: Problem with connection to Apstra server: '{apstra_server_name}'")
            logger.critical(e)
            exit(1)
        
        if login['token'] is not None:
            self.controller.platform = self.apstra.platform.get_version()
            self.apstra.internal.copy_dataclass(self.controller, self.handlers.apstra[apstra_server_name])
            logger.info(f"APSTRA: Active Controller {self.controller.name} ({self.controller.host})")

        return(self.controller)

    def session(self, apstra_server_name=None):
        logger.info(f"APSTRA: Change server connection session '{self.controller.name} -> {apstra_server_name}'")
        self.apstra.internal.copy_dataclass(self.handlers.apstra[apstra_server_name], self.controller)
        return (self.controller)
        
    def get_token(self, apstra_server_name):
        return(self.handlers.apstra[apstra_server_name].rest.token)
    
    def change_blueprint(self, bp_name) -> ActiveBlueprint:
        try:
            bp:ActiveBlueprint = self.parameters.bp_cache['bp_name']
            # If active controller is diffrent then pointed inside cache BP info / we will connect to propere controller
            if self.parameters.active_controller != bp.controller:
                self.connect(bp.controller)
            return(bp)
        except:
            logger.debug(f"APSTRA: Change bluprint based on cached failed / not found cache information about = '{bp_name}' - will need to query information from active connected controller")
            pass
        
        bp = self.apstra.blueprint.get(bp_name)
        if bp is None:
            logger.critical(f"EXIT: Bluprint: '{bp_name}' not found on Apstra server: '{self.parameters.active_controller}'")
            raise ErrorApstraAPI(f"{self.parameters.active_controller} -> {bp_name}", 404)
        else:
            logger.info(f"APSTRA: Change blueprint to '{bp.label}'")
            logger.debug(f"APSTRA: self.parameters.bp = '{bp}'")
            active_bp  = ActiveBlueprint(id=bp.id, label=bp.label, controller=self.parameters.active_controller)
            self.parameters.active_bp = active_bp
            # Store info about mapping bp_lable=>bp_id to prevent future queries
            self.parameters.bp_cache[bp.label] = active_bp
        return(self.parameters.active_bp)

