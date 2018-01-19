#!/usr/bin/env python

# Copyright (c) 2018 Philip Bove <pgbson@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import *

try:
	from infoblox_client import objects, connector, exceptions
	HAS_INFOBLOX_CLIENT = True
except ImportError:
	HAS_INFOBLOX_CLIENT = False

def ea_to_dict(extattrs):
	if extattrs:
		return extattrs.__dict__['_ea_dict']
	else:
		return {}

def delete_a_record(module, a_record):
	try:
		if a_record:
			a_record.delete()
			module.exit_json(changed=True)
		else:
			module.exit_json(changed=False)
	except exceptions.InfobloxException as error:
		module.fail_json(msg=str(error))


def create_a_record(conn, module, a_record):
	try:
		if module.params['extattrs']:
			extattrs = objects.EA(module.params['extattrs'])
		else:
			extattrs = None
		if a_record:
			module.exit_json(changed=False, ip_addr=a_record.ipv4addr, name=a_record.name)
		
		objects.ARecord.create(conn,ip=module.params['ip_address'],name=module.params['name'] ,
			view=module.params['dns_view'],extattrs=extattrs)
		#ARecord.create does not return the ip address etc. so we must seach for it again
		a_record = objects.ARecord.search(conn, name=module.params['name'], ipv4addr=module.params['ip_address'])
		module.exit_json(changed=True, name=a_record.name, ip_addr=a_record.ipv4addr, extattrs=ea_to_dict(a_record.extattrs))

	except exceptions.InfobloxException as error:
		module.fail_json(msg=str(error))


def main():

	module = AnsibleModule(
			argument_spec = dict(
				host = dict(type='str' ,required=True),
				name = dict(type='str', required=True),
				ip_address = dict(type='str',required=True),
				username= dict(type='str', required=True),
				password = dict(type='str', required=True, no_log=True),
				validate_certs = dict(type='bool', choices=[True,False], default=True, required=False),
				state = dict(type='str',choices=['present','absent'], default='present', required=False),
				wapi_version = dict(type='str', default='2.2', required=False),
				extattrs = dict(type='dict', default=None, required=False),
				dns_view = dict(type='str',required=True)
			),
			supports_check_mode=False
		)

	if not HAS_INFOBLOX_CLIENT:
		module.fail_json(msg='infoblox-client is not installed.  Please see details here: https://github.com/infobloxopen/infoblox-client')
	
	try:
		conn = connector.Connector({'host':module.params['host'],'username':module.params['username'],'password':module.params['password'],
			'ssl_verify':module.params['validate_certs'],'wapi_version':module.params['wapi_version']})
		a_record = objects.ARecord.search(conn, name=module.params['name'],ipv4addr=module.params['ip_address'])

		if module.params['state'] == 'present':
			create_a_record(conn, module, a_record)
		else:
			delete_a_record(module, a_record)
	except exceptions.InfobloxException as error:
		module.fail_json(msg=str(error))

if __name__ == '__main__':
	main()