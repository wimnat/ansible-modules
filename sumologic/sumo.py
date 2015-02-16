#!/usr/bin/python

import platform
import os
import shutil

class Sumo(object):

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(Sumo, args, kwargs)

    def __init__(self, module):
        self.module     = module
        self.changed    = False
        self.state      = module.params['state']
        self.clean      = module.params['clean']
        self.name       = module.params['name']
        self.email      = module.params['email']
        self.password   = module.params['password']
        self.accessid   = module.params['accessid']
        self.accesskey  = module.params['accesskey']
        self.sources    = module.prarms['sources']
        self.override   = module.params['override']
        self.ephemeral  = module.params['ephemeral']
        self.clobber    = module.params['clobber']
        self.err        = ""
        self.out        = ""

    def is_installed(self):
        return self.is_installed()

    def install(self):
        return self.install()

    def uninstall(self):
        return self.uninstall()
    
    def api_delete_collector(self, collectorId):
        
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, "https://api.sumologic.com/api/v1", self.accessid, self.accesskey)
        
        
        url = "https://api.sumologic.com/api/v1/collectors/" + collectorId
        headers = {'content-type': 'application/json'}
        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPHandler, urllib2.HTTPBasicAuthHandler(password_mgr)))
        req = urllib2.Request(url, None, headers)
        req.get_method = lambda: 'DELETE'
        response, info = urllib2.urlopen(req)
        

class WindowsSumo(Sumo):
    platform = 'Windows'
    distribution = None

    def is_installed(self):
        if os.path.exists("C:\sumo"):
            return True
        else:
            return False



class LinuxSumo(Sumo):
    platform = 'Linux'
    distribution = None

    def is_installed(self):
        if os.path.exists("/opt/SumoCollector/collector"):
            return True
        else:
            return False

    def install(self):
        if self.is_installed():
            # nothing to do
            self.changed = False
        else:
            # do the install
            if platform.machine() == 'i386': # 32-bit
                rc, out, err = self.module.run_command("curl https://collectors.sumologic.com/rest/download/linux/32 -o /tmp/sumo-install.sh --connect-timeout 30")
            elif platform.machine() == 'x86_64': # 64-bit
                rc, out, err = self.module.run_command("curl https://collectors.sumologic.com/rest/download/linux/64 -o /tmp/sumo-install.sh --connect-timeout 30")
                
            try:
                if rc != 0:
                    raise EnvironmentError("There was a problem downloading the collector")
                rc, out, err = self.module.run_command("chmod +x /tmp/sumo-install.sh")
                rc, out, err = self.module.run_command("bash /tmp/sumo-install.sh -q")
                if rc != 0:
                    raise EnvironmentError("There was a problem installing the collector")
                self.changed = True
                self.out = out
                self.err = err
            finally:
                self.module.run_command("rm -f /tmp/sumo-install.sh")
                
            # If clean flag True then delete the created collector so it can be recreated when necessary
            if self.clean == True:
                # Stop the collector
                self.module.run_command("service collector stop")
                # Get the collector ID
                f = open("/opt/SumoCollector/config/creds/main.properties")
                for line in f:
                    if "apiId" in line:
                        collectorIdLine = line.split("=")
                        collectorId = collectorIdLine[1]
                        break
                # Delete the local creds
                os.remove("/opt/SumoCollector/config/creds/main.properties")
                # Delete the collector via the Sumo API
                self.api_delete_collector(collectorId)
                

    def uninstall(self):
        if not self.is_installed():
            # nothing to do
            self.changed = False
        else:
            # do the uninstall
            rc, out, err = self.module.run_command("/bin/bash /opt/SumoCollector/uninstall -q")
            if rc != 0:
                raise EnvironmentError("There was a problem uninstalling the collector")
            self.changed = True



def main():

    module = AnsibleModule(
        argument_spec = dict(
            state = dict(required=True, choices=['present', 'absent'], type='str')
            clean = dict(default="no", type='bool')
            name = dict(type='str')
            email = dict(type='str')
            password = dict(type='str')
            accessid = dict(type='str')
            accesskey = dict(type='str')
            sources = dict(type'str')
            override = dict(type='bool')
            ephemeral = dict(type='bool')
            clobber = dict(type='bool')
        ),
        supports_check_mode=False
    )

    sumo = Sumo(module)
    result = {}
    result['changed'] = False

    try:

        if sumo.state == 'present':
            result['do_install'] = "yes"
            sumo.install()
        elif sumo.state == 'absent':
            sumo.uninstall()

        result['changed'] = sumo.changed
        result['out'] = sumo.out
        result['err'] = sumo.err

        module.exit_json(**result)

    except RuntimeError as e:
        module.fail_json(msg=str(e))
    except EnvironmentError as e:
        module.fail_json(msg=str(e))


# import module snippets
from ansible.module_utils.basic import *
main()
