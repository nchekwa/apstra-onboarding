#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from apstra.dao import Handlers, Controller, Parameters

class Apstra:
    def __init__(self):
        self.handlers = Handlers()
        self.parameters = Parameters()
        self.controller = Controller()
        
        from apstra.client import Client as ApstraClient
        from apstra.internal import Internal as ApstraInternal
        from apstra.tasks import Tasks as ApstraTasks
        from apstra.rest import Rest as ApstraRest
        
        self.client     = ApstraClient(self)
        self.internal   = ApstraInternal(self)
        self.tasks      = ApstraTasks(self)
        self.rest       = ApstraRest(self)
        
        from .platform import Platform as ApstraPlatform
        from .resources import Resources as ApstraResources
        from .blueprint import Blueprint as ApstraBlueprint

        self.platform   = ApstraPlatform(self)
        self.resources  = ApstraResources(self)
        self.blueprint  = ApstraBlueprint(self)