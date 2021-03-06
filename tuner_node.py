from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import argparse
import validators as valid

import hpo.bandit_config as bconf

from ws.shared.read_cfg import *
from ws.shared.logger import * 

from ws.apis import wait_hpo_request


def main(run_config):
    try:
        if not bconf.validate(run_config):
            raise ValueError('Invaild HPO configuration.')    

        master_node = None
        if "master_node" in run_config:
            m_conf = run_config['master_node']
            if not 'url' in m_conf:
                raise ValueError("Invalid configuration. No URL information of master node")
            if valid.url(m_conf['url']):
                master_node = m_conf['url']
                if master_node.endswith('/'):
                    master_node += master_node[:-1]
            else:
                raise ValueError("Invalid master URL: {}".format(m_conf['url']))

        debug_mode = False
        if "debug_mode" in run_config:
            if run_config["debug_mode"]:
                debug_mode = True
                set_log_level('debug')
                print_trace()

        hp_config_dir = "./hp_conf/"
        if "hp_config_dir" in run_config:
            hp_config_dir = run_config["hp_config_dir"]         
       
        hp_cfg_file = run_config["hp_config"]
        hp_cfg_path = '{}{}.json'.format(hp_config_dir, hp_cfg_file)
        hp_cfg = read_hyperparam_config(hp_cfg_path)

        port = 5000
        if "port" in run_config:
            port = run_config["port"]

        credential = None
        if "credential" in run_config:
            credential = run_config['credential']
        else:
            raise ValueError("No credential info in run configuration")

        debug("HPO node will be ready to serve...")
        wait_hpo_request(run_config, 
                         hp_cfg, 
                         debug_mode=debug_mode, 
                         port=port,
                         credential=credential, 
                         master_node=master_node)
    
    except KeyboardInterrupt as ki:
        warn("Terminated by Ctrl-C.")
        sys.exit(-1) 

    except Exception as ex:
        error("Exception ocurred: {}".format(ex))


if __name__ == "__main__":
    run_conf_path = './run_conf/'    
    parser = argparse.ArgumentParser()
    parser.add_argument('-rd', '--rconf_dir', default=run_conf_path, type=str,
                        help='Run configuration directory.\n'+\
                        'Default setting is {}'.format(run_conf_path))
    parser.add_argument('run_config', type=str, help='Run configuration name.')
    args = parser.parse_args()
    run_cfg = read_run_config(args.run_config, args.rconf_dir)    
    
    main(run_cfg)