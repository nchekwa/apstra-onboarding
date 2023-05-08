#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import sys
sys.dont_write_bytecode = True
from signal import signal, SIGINT

from pprint import pprint

import yaml
import argparse

from boarding import BoardingAOS

def signal_handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(1)



stdout_lvl='INFO'


############################################################################################################################
############################################################################################################################
############################################################################################################################
if __name__ == '__main__':
    signal(SIGINT, signal_handler) 
    
    parser = argparse.ArgumentParser(prog='onboarding.py')
    parser.add_argument('-c', '--config', help='YAML File with configuration', default='config.yaml')
    parser.add_argument('-d', '--debug', help='Debug Screen Output Level [default: INFO]', default='INFO')
    args = parser.parse_args()
    kwargs = vars(args)
    stdout_lvl=kwargs['debug']
    
    print('[    INFO] Running. Press CTRL-C to exit.')
    
    
    Boarding = BoardingAOS()
    
    # Get Run ID
    # ID avalible under > Boarding.parameter.id
    Boarding.internal.get_id()
    
    # Init Logger
    # logger: info, critical, warning, debug, error
    logger = Boarding.internal.logger(stdout_lvl)
    
    # Read YAML config
    # config avalible under > Boarding.parameter.config
    Boarding.config.get("configs/"+kwargs['config'])
    logger.debug("Config: \n"+yaml.dump(Boarding.config.redacted()))

    # Boarding resource Config part
    logger.info(Boarding.internal.generate_line(150))
    Boarding.boarding.resorces_create()


    # Start Analyse Blueprint Config
    logger.info(Boarding.internal.generate_line(150))
    Boarding.sync.run()


    logger.info(Boarding.internal.generate_line(150))
    Boarding.boarding.run()

    Boarding.internal.save_parameters()

    #Boarding.apstra.blueprint.revert('03d43c6d-e171-4d61-86a9-dd782dd640cd')
    #Boarding.apstra.blueprint.revert('5558baca-3c49-4be9-8de9-581bc89cf794')
    #pprint(Boarding.parameter.sync)