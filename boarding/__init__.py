#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys, os
sys.dont_write_bytecode = True

import logging
logger = logging.getLogger(__name__)

from timeit import default_timer as timer
from dataclasses import dataclass, field
from pprint import pprint


from apstra import Apstra

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    
class BoardingAOS():
    def __init__(self):
        self.start = timer()    
        
        self.apstra     = Apstra()         
        self.parameters  = self.apstra.parameters
        self.handlers  = self.apstra.handlers
        
        from .internal import Internal as BoardingInternal
        from .config import Config as BoardinConfig
        from .sync import Sync as BoardingSync
        from .boarding import Boarding as BoardingCore
        self.internal   = BoardingInternal(self)
        self.config     = BoardinConfig(self)
        self.sync       = BoardingSync(self)
        self.boarding   = BoardingCore(self)
        

        
        




