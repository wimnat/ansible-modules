#!/usr/bin/python

import platform
import os
import shutil
import urllib2
import base64
import hashlib

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
        self.sources    = module.params['sources']
        self.syncSources    = module.params['syncSources']
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
    
    def api_create_request(self, url):

        print url
        base64string = base64.b64encode(self.accessid + ":" + self.accesskey)
        headers = {'content-type': 'application/json', 'Authorization': 'Basic %s' % base64string}
        return urllib2.Request(url, None, headers)

    def api_get_collectors(self):

        req = self.api_create_request("https://api.sumologic.com/api/v1/collectors")
        response = urllib2.urlopen(req)
        data = json.load(response)
        print data


    def api_delete_collector(self, collectorId):

        base64string = base64.b64encode(self.accessid + ":" + self.accesskey)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        headers = {'Authorization': 'Basic %s' % base64string}
        req = urllib2.Request("https://api.sumologic.com/api/v1/collectors/" + collectorId + "/", None, headers)


        #req = self.api_create_request("https://api.sumologic.com/api/v1/collectors/" + collectorId)
        req.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(req)
        data = json.load(response)
        print data
        
    def sumo_conf(self, path):
        
        try:
            # Create a temp sumo.conf for comparison
            f = open(path + ".tmp", 'w+')
            # Write each conf value to file
            if self.name:
                f.write("name=" + self.name + "\n")
            if self.email:
                f.write("email=" + self.email + "\n")
            if self.password:
                f.write("password=" + self.password + "\n")
            if self.accessid:
                f.write("accessid=" + self.accessid + "\n")
            if self.accesskey:
                f.write("accesskey=" + self.accesskey + "\n")
            if self.sources:
                f.write("sources=" + self.sources + "\n")
            if self.syncSources:
                f.write("syncSources=" + self.syncSources + "\n")
            if self.override:
                f.write("override=" + str(self.override) + "\n")
            if self.ephemeral:
                f.write("ephemeral=" + str(self.ephemeral) + "\n")
            if self.clobber:
                f.write("clobber=" + str(self.clobber) + "\n")

            f.close()

            # Compare files
            if ((hashlib.md5(open(path + ".tmp", 'rb').read()).hexdigest()) != (hashlib.md5(open(path, 'rb').read()).hexdigest())):
                shutil.copy(path + ".tmp", path)
                self.changed = True
        finally:
            os.remove(path + ".tmp")
        

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
    conf_path = "/etc/sumo.conf"
    distribution = None

    def set_sumo_conf(self):
        self.sumo_conf(self.conf_path)

    def is_installed(self):
        if os.path.exists("/opt/SumoCollector/collector"):
            return True
        else:
            return False

    def install(self):
        if not self.is_installed():
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
                #print "collector id = " + collectorId
                #self.api_delete_collector(collectorId)
                

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
            state = dict(required=True, choices=['present', 'absent'], type='str'),
            clean = dict(default="no", type='bool'),
            name = dict(type='str'),
            email = dict(type='str'),
            password = dict(type='str'),
            accessid = dict(type='str'),
            accesskey = dict(type='str'),
            sources = dict(type='str'),
            syncSources = dict(type='str'),
            override = dict(type='bool'),
            ephemeral = dict(type='bool'),
            clobber = dict(type='bool')
        ),
        mutually_exclusive = [ 
                               ['email', 'accessid'],
                               ['password', 'accesskey'],
                               ['sources', 'syncSources']
                             ],
        supports_check_mode=False
    )

    sumo = Sumo(module)
    result = {}
    result['changed'] = False

    try:

        if sumo.state == 'present':
            result['do_install'] = "yes"
            #sumo.api_delete_collector("100010919")
            sumo.set_sumo_conf()
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
