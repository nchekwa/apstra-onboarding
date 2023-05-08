import os
import requests
import http

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime


# #################################################################################################
# DAO -> Data Access Object
# #################################################################################################
# MAIN >
@dataclass
class Log:
    path: str = None
    file_path: str = None

@dataclass
class ActiveBlueprint:
    '''
    Bluprint: 
        bp.id,
        bp.label
        bp.controller
    '''
    id: str = None
    label: str = None
    controller: str = None

@dataclass
class Parameters:
    id: str = None
    active_bp: ActiveBlueprint = field(default_factory=ActiveBlueprint)
    active_controller: str = None
    bp_cache: Dict[str, int] = field(default_factory=dict)
    systems: Dict[str, int] = field(default_factory=dict)
    current_dir: str = os.getcwd()
    config: Dict[str, int] = field(default_factory=dict)
    sync: Dict[str, int] = field(default_factory=dict)
    log: Log = Log()
    
    
        
@dataclass
class Controller:
    name: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    protocol: str = 'https'
    port: int = 443
    ssl_validation: bool = False
    session: requests = requests.Session()
    user_uuid: Optional[str] = None
    timeout: int = 5
    platform: object = None
    blueprints: Optional[str] = None
    
    def __post_init__(self):
        if self.protocol not in ['http', 'https']:
            raise ValueError("Invalid protocol. Valid values are 'http' or 'https'.")     


@dataclass
class Handlers:
    apstra: Dict[str, int] = field(default_factory=dict)
    logger: object = None

# Reponse >
@dataclass
class ID:
    id: str = None

@dataclass
class HttpStatus:
    status_code: int
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.description is None:
            self.description = http.HTTPStatus(self.status_code).phrase

###################################################################################################
# ApstraRef -> Resources -> IPv4Pool
@dataclass
class IPv4Subnet:
    status: str = "pool_element_available"
    total: Optional[str] = None
    network: Optional[str] = None
    used: Optional[str] = None
    used_percentage: Union[int, float, None] = 0.0

@dataclass
class IPv4Pool:
    status: str = "not_in_use"
    subnets: List[IPv4Subnet] = None
    used: Optional[str] = None
    display_name: Optional[str] = None
    tags: List[str] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    used_percentage: Union[int,float,None] = None
    total: Optional[str] = None
    id: Optional[str] = None

###################################################################################################
# ApstraRef -> Resources -> AsnPool / VniPool
@dataclass
class PoolRange:
    status: str = "pool_element_available"
    used: Optional[str] = None
    last: Optional[int] = None
    used_percentage: Union[int,float,None] = None
    total: Optional[str] = None
    first: Optional[int] = None

@dataclass
class AsnPool:
    status: str = "not_in_use"
    used: Optional[str] = None
    display_name: Optional[str] = None
    tags: List[str] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    ranges: List[PoolRange] = None
    used_percentage: Union[int,float,None] = None
    total: Optional[str] = None
    id: Optional[str] = None

@dataclass
class VniPool:
    status: str = "not_in_use"
    used: Optional[str] = None
    display_name: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    ranges: Optional[List[PoolRange]] = None
    used_percentage: Optional[float] = None
    total: Optional[str] = None
    id: Optional[str] = None

###################################################################################################
# ApstraRef -> Route-Policy
@dataclass
class ExportPolicy:
    static_routes: bool = field(default=False)
    loopbacks: bool = field(default=True)
    spine_superspine_links: bool = field(default=False)
    l3edge_server_links: bool = field(default=True)
    spine_leaf_links: bool = field(default=True)
    l2edge_subnets: bool = field(default=True)

@dataclass
class ExtraRoute:
    action: Optional[str] = None
    prefix: Optional[str] = None
    le_mask: Union[None, int] = None
    ge_mask: Union[None, int] = None


@dataclass
class RoutePolicy:
    export_policy: ExportPolicy = ExportPolicy()
    description: Optional[str] = None
    expect_default_ipv4_route: bool = field(default=False)
    extra_export_routes: List[ExtraRoute] = field(default_factory=list)
    aggregate_prefixes: List[str] = field(default_factory=list)
    label: Optional[str] = None
    policy_type: Optional[str] = None
    expect_default_ipv6_route: bool = False
    extra_import_routes: List[ExtraRoute] = field(default_factory=lambda: [])
    id: Optional[str] = None
    import_policy: Optional[str] = None
    
    
###################################################################################################
# ApstraRef -> AsyncResponse
@dataclass
class AsyncResponse:
    id: str
    task_id: str
    task_status: str
    task_processing_time: float
    
###################################################################################################
# ApstraRef -> Tag
@dataclass
class Tag:
    id: Optional[str]
    description: Optional[str]
    label: Optional[str]

###################################################################################################
# ApstraRef -> BlueprintInfo
@dataclass
class DeploymentStatus:
    num_failed: int
    num_pending: int
    num_succeeded: int

@dataclass
class DeploymentModesSummary:
    deploy: int
    drain: int
    ready: int
    undeploy: int

@dataclass
class AnomalyCounts:
    all: int
    arp: int
    bgp: int
    blueprint_rendering: int
    cabling: int
    config: int
    counter: int
    deployment: int
    hostname: int
    interface: int
    lag: int
    liveness: int
    mac: int
    mlag: int
    probe: int
    route: int
    series: int
    streaming: int

@dataclass
class DeploymentStatuses:
    discovery2_config: DeploymentStatus
    drain_config: DeploymentStatus
    service_config: DeploymentStatus

@dataclass
class BlueprintInfo:
    access_count: int
    anomaly_counts: AnomalyCounts
    build_errors_count: int
    build_warnings_count: int
    deploy_modes_summary: DeploymentModesSummary
    deployment_status: DeploymentStatuses
    design: str
    external_router_count: int
    generic_count: int
    has_uncommitted_changes: bool
    id: str
    l2_server_count: int
    l3_server_count: int
    label: str
    last_modified_at: str
    leaf_count: int
    remote_gateway_count: int
    root_cause_count: int
    spine_count: int
    status: str
    superspine_count: int
    top_level_root_cause_count: int
    version: int
    
###################################################################################################
# ApstraRef -> RoutingZone
@dataclass
class RTPolicy:
    import_RTs: Optional[str] = None
    export_RTs: Optional[str] = None

@dataclass
class RoutingZone:
    sz_type: str = "evpn"
    vni_id: Optional[int] = field(
        default=None,
        metadata={
            "validate": (
                lambda v: v is None or (v >= 4096 and v <= 16777214),
                "Value should be None or at least 4096 and at most 16777214."
            )
        }
    )
    route_target: Optional[str] = None
    routing_policy_id: Optional[str] = None 
    routing_policy: Union[object,str,None] = None
    label: str = ""
    vrf_name: str = field(
        default="default",
        metadata={
            "validate": (
                lambda v: (
                    len(v) >= 1 and len(v) <= 15 and 
                    all(c.isalnum() or c in ["_", "-"] for c in v)
                ),
                "Length should be at least 1 and at most 15. "
                "Invalid routing zone name. Only ASCII alphanumeric "
                "characters, underscore and dash are allowed."
            )
        }
    )
    rt_policy: Optional[RTPolicy] = None
    id: Optional[str] = None
    vlan_id: Optional[int] = None

    def to_dict(self):
        return asdict(self)

###################################################################################################
# ApstraRef -> Conectivity Template [ObjPolicy]
@dataclass
class ObjPolicy:
    id: Optional[str] = None
    label: Optional[str] = None
    policy_type_name: Optional[str] = None
    description: Optional[str] = None
    subpolicies: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    user_data: Optional[str] = None
    visible: Optional[bool] = None
    
    
###################################################################################################
# ApstraRef -> Virtual Network
@dataclass
class BoundTo:
    access_switch_node_ids: List[str] = field(default_factory=list)
    system_id: Optional[str] = None
    system: Optional[str] = None
    vlan_id: Optional[int] = None

@dataclass
class VirtualNetwork:
    id: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    vn_type: Optional[str] = None
    vn_id: Optional[str] = None
    vlan_id: Optional[str] = None
    reserved_vlan_id: Optional[int] = None
    security_zone: Optional[str] = None
    routing_zone: Optional[str] = None
    security_zone_id: Optional[str] = None
    route_target: Optional[str] = None
    rt_policy: Optional[str] = None
    dhcp_service: Optional[str] = None
    ipv4_enabled: Optional[bool] = None
    ipv4_subnet: Optional[str] = None
    virtual_gateway_ipv4: Optional[str] = None
    virtual_gateway_ipv4_enabled: Optional[bool] = None
    ipv6_enabled: Optional[bool] = None
    ipv6_subnet: Optional[str] = None
    virtual_gateway_ipv6: Optional[str] = None
    virtual_gateway_ipv6_enabled: Optional[bool] = None
    virtual_mac: Optional[str] = None
    bound_to: List[BoundTo] = None

    def __post_init__(self):
        if self.routing_zone is not None:
            self.security_zone = self.routing_zone
        if self.security_zone is not None:
            self.routing_zone = self.security_zone

    def __repr__(self):
        props = [f"{k}={v}" for k, v in self.__dict__.items() if v is not None]
        return f"{self.__class__.__name__}({', '.join(props)})"
    
    #@property
   # def routing_zone(self):
    #    return self.security_zone
    
    #@routing_zone.setter
    #def routing_zone(self, value):
    #    self.security_zone = value