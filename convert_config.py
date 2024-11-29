#!/usr/bin/env python3
import yaml
import sys

def convert_config(input_file, output_file):
    with open(input_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Convert ip_prefixes to new prefixes format
    if 'ip_prefixes' in config:
        v4_prefixes = [p for p in config['ip_prefixes'] if ':' not in p]
        v6_prefixes = [p for p in config['ip_prefixes'] if ':' in p]
        config['prefixes'] = {
            'v4': v4_prefixes[0] if v4_prefixes else '100.64.0.0/10',
            'v6': v6_prefixes[0] if v6_prefixes else 'fd7a:115c:a1e0::/48',
            'allocation': 'sequential'
        }
        del config['ip_prefixes']
    
    # Convert DNS config
    if 'dns_config' in config:
        dns = {
            'magic_dns': config['dns_config'].get('magic_dns', True),
            'override_local_dns': config['dns_config'].get('override_local_dns', True),
            'base_domain': config['dns_config'].get('base_domain', 'example.com'),
            'nameservers': {
                'global': config['dns_config'].get('nameservers', []),
                'split': config['dns_config'].get('restricted_nameservers', {})
            },
            'search_domains': config['dns_config'].get('domains', []),
            'extra_records': config['dns_config'].get('extra_records', [])
        }
        config['dns'] = dns
        del config['dns_config']
    
    # Convert database config
    db_config = {
        'type': 'sqlite' if config.get('db_type') == 'sqlite3' else config.get('db_type', 'sqlite'),
        'debug': False,
        'gorm': {
            'prepare_stmt': True,
            'parameterized_queries': True,
            'skip_err_record_not_found': True,
            'slow_threshold': 1000
        },
        'sqlite': {
            'path': config.get('db_path', '/var/lib/headscale/db.sqlite'),
            'write_ahead_log': True
        }
    }
    
    if config.get('db_type') == 'postgres':
        db_config['postgres'] = {
            'host': config.get('db_host', 'localhost'),
            'port': config.get('db_port', 5432),
            'name': config.get('db_name', 'headscale'),
            'user': config.get('db_user', ''),
            'pass': config.get('db_pass', ''),
            'ssl': config.get('db_ssl', False),
            'max_open_conns': 10,
            'max_idle_conns': 10,
            'conn_max_idle_time_secs': 3600
        }
    
    config['database'] = db_config
    
    # Remove old database keys
    for key in ['db_type', 'db_path', 'db_host', 'db_port', 'db_name', 'db_user', 'db_pass', 'db_ssl']:
        if key in config:
            del config[key]
    
    # Add policy section if ACL path exists
    if 'acl_policy_path' in config:
        config['policy'] = {
            'mode': 'file',
            'path': config.get('acl_policy_path', '')
        }
        del config['acl_policy_path']

    with open(output_file, 'w') as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: convert_config.py input_file output_file")
        sys.exit(1)
    
    convert_config(sys.argv[1], sys.argv[2])
