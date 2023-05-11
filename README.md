<h1>This project contains two libs:</h1>

* <i>apstra</i> -  python lib which is dedicated to standardising API calls to the Juniper Apstra system (tested with 4.1.2).
* <i>boarding</i> - python lib which is using 'apstra' as a backend for executing commands based on YAML configuration
<br>

<h3>Othere content</h3>

* <i>apstra-jupyter_docs</i> - docs in Jupyter standard which can be used to get some base knowledge how to use <i>'apstra'</i> lib
* <i>config</i> - contains configuration YAML file / or folders - which are used by <i>"onboarding.py"</i> script
* <i>schemas</i> - contains Draft7 json schema for validate YAML config files
* <i>templates</i> - contains <i>'apstra'</i> lib jinja template dedicated to having an easy way of generating the content of commands sent to Apstra API service.

<h1>onboarding.py</h1>
Description:

```bash
# python3 onboarding.py  -h
usage: onboarding.py [-h] [-c CONFIG] [-d DEBUG]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        YAML File (or dir) with configuration
  -d DEBUG, --debug DEBUG
                        Debug Screen Output Level [default: INFO]
```
How to run:
```bash
onboarding.py -c ApstraDemo
```
<h2>What it will do?</h2>

- run validation of config file: check Draft7 validation, merge yaml file (if you are using folder content)<br>
[if you use dir: anchorn should be ALWAYS extracted to seperate file]<br>
- run sync process which will take config elements for compare between:<br>
&nbsp; &nbsp; &nbsp; &nbsp; YAML config file <--and--> Apstra server<br>
(configuration elements: routing_policies, nodes, connectivity_template, virtual_network, self.routing_zones)
- if under blueprint 'sync' option would be set as True - config elements which not exist in configu YAML, and exist on Apstra server -> <u>would be removed from</u> Apstra server
- next would be trigere bording process: (routing_zones, virtual_network, connectivity_template, nodes, nodes_interface_speed, nodes_connectivity_template_assign)

<h2>What it will NOT do?</h2>

- this is just Day-2 provisioning script - if you modyfie some parameters like name or vlan id - it will not be "sync" (will not update config on Apstra)
- if you use sync=True - please be aware that element not listed in configuration would be removed from Apstra




<h2>Main Features:</h2>

- YAML config validate by Draft7 schema
- YAML will not use element IDs but only names/labels
- configuration can be stored in multiple YAML files with anachors references (ie. same vlan for multiple blueprints)
- create resource (asn/ip/vni)
- create blueprints sub elements of Day2 configuration across multiple Bluprints on multiple Apstra Controllers
- create blueprint -> routing-zones
- create blueprint -> virtual-networks (bound to name of phisical swtich (leaf and access) which are translate to redundancy-groups)
- create blueprint -> connectivity-templates (single vlan / multivlan / bgp L3 peering / any othere predefined in jinja template file)
- create blueprint -> nodes (generic or external + links to leaf [Physical  or LAG])
- create blueprint -> nodes (change speed interface if needed)
- assign tags to CT/NODEs/RESOURCEs
- assign node interfaces to assign connectivity-templates to Physical or LAG interface (pointing server interface and then CT provision on Leaf interface side)
- store logging for each run of script in seperate log file


<h2>Todo:</h2>

- create routing-policies
- 'sync=True' option will allow to remove elements on Apstra which are not defined in YAML file
- 'sync=True' will not remove elements from Apstra server (tagged as 'protect' will be keep on apstra side)
- add option -commit for script which will Commit Configuration only if blueprint not repors any errors

