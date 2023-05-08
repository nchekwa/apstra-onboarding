from collections import namedtuple
from typing import Tuple

class Platform:
    from . import Apstra
    
    def __init__(self, main_class: Apstra) :
        self.apstra = main_class
        self.controller = main_class.controller

    # #################################################################################################################
    # GET
    #
    def get_version(self) -> Tuple:
        uri_version_path = "/api/version"
        uri_server_path = "/api/versions/server"

        aos_ver = self.apstra.rest.get_json_response(uri_version_path)
        server_ver = self.apstra.rest.get_json_response(uri_server_path)

        ApstraVersion = namedtuple("Apstra", [ "version", "major", "minor",  "build", "full"])
        
        self.controller.version = ApstraVersion(
            version=aos_ver["version"],
            major=aos_ver["major"],
            minor=aos_ver["minor"],
            build=aos_ver["build"],
            full=server_ver["version"]
        )
        return(self.controller.version)