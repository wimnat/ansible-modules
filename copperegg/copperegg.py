#!/usr/bin/python

import platform
import os
import shutil
import urllib2
import base64
import hashlib

# needed
import time
import subprocess

class Copperegg(object):

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(Copperegg, args, kwargs)

    def __init__(self, module):
        self.module     = module
        self.changed    = False
        self.state      = module.params['state']
        self.api_key  = module.params['api_key']
        self.tags  = module.params['tags']
        self.label  = module.params['label']
        self.err        = ""
        self.out        = ""

    def is_installed(self):
        return self.is_installed()

    def install(self):
        return self.install()

    def uninstall(self):
        return self.uninstall()
    
        

class WindowsCopperegg(Copperegg):
    platform = 'Windows'
    distribution = None

    def is_installed(self):
        if os.path.exists("C:\sumo"):
            return True
        else:
            return False



class LinuxCopperegg(Copperegg):
    platform = 'Linux'
    distribution = None

    def is_installed(self):
        if os.path.exists("/usr/local/revealcloud/revealcloud"):
            return True
        else:
            return False

    def install(self):
        if not self.is_installed():
            # do the install
            #rc, out, err = self.module.run_command("curl -sk --connect-timeout 30 http://%s@api.copperegg.com/rc.sh | sh" % self.api_key, shell=True)
            try:
                devnull = open(os.devnull, 'w')
                p = subprocess.Popen("curl -sk http://%s@api.copperegg.com/rc.sh | RC_TAG=%s RC_LABEL=%s sh" % (self.api_key, ','.join(self.tags), self.label), shell=True, stdout=devnull, stderr=devnull)    
                if p.returncode is not 0:
                    raise
                else:
                    self.changed=True
                #p2 = subprocess.Popen(["sh"], stdin=p1.stdout, stdout=subprocess.PIPE)
                #p1.stdout.close()
                #p2.communicate()
            except Exception as e:
                self.module.fail_json(msg=e)
            #if rc != 0:
            #    raise EnvironmentError("There was a problem installing the collector err: %s out: %s" % (err, out))
            #else:
            #    self.changed = True    
                

    def uninstall(self):
        if not self.is_installed():
            # nothing to do
            self.changed = False
        else:
            # do the uninstall
            try:
                rc, out, err = self.module.run_command("service revealcloud stop")
                time.sleep(2)
                rc, out, err = self.module.run_command("/usr/local/revealcloud/revealcloud -R -k %s" % self.api_key)
                if rc != 0:
                    raise EnvironmentError("There was a problem removing the server in the CopperEgg cloud %s" % out)
            #try:
                shutil.rmtree("/usr/local/revealcloud")
                os.remove("/etc/init.d/revealcloud")
                if os.path.exists("/etc/init/revealcloud.conf"):
                    os.remove("/etc/init/revealcloud.conf")
                else:
                    os.remove("/etc/rc.d/rc1.d/K99revealcloud")
                    os.remove("/etc/rc.d/rc2.d/S99revealcloud")
                    os.remove("/etc/rc.d/rc3.d/S99revealcloud")
                    os.remove("/etc/rc.d/rc4.d/S99revealcloud")
                    os.remove("/etc/rc.d/rc5.d/S99revealcloud")
                    os.remove("/etc/rc.d/rc6.d/K99revealcloud")
            except OSError:
                pass
            except Exception as e:
                raise EnvironmentError("There was a problem removing revealcloud directory and files %s" % e)
            
            rc, out, err = self.module.run_command("userdel -r revealcloud")
            if rc != 0:
                raise EnvironmentError("There was a problem removing the revealcloud user")
            
            self.changed = True



def main():

    module = AnsibleModule(
        argument_spec = dict(
            state = dict(required=True, choices=['present', 'absent'], type='str'),
            api_key = dict(required=True, type='str'),
            tags = dict(required=False, default=[], type='list'),
            label = dict(required=False, default='', type='str')
        ),
        supports_check_mode=False
    )

    copperegg = Copperegg(module)
    result = {}
    result['changed'] = False
    
    try:

        if copperegg.state == 'present':
            copperegg.install()
        elif copperegg.state == 'absent':
            copperegg.uninstall()

        result['changed'] = copperegg.changed
        result['out'] = copperegg.out
        result['err'] = copperegg.err

        module.exit_json(**result)

    except RuntimeError as e:
        module.fail_json(msg=str(e))
    except EnvironmentError as e:
        module.fail_json(msg=str(e))


# import module snippets
from ansible.module_utils.basic import *
import shutil
main()
