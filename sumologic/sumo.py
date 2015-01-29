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
        self.err        = ""
        self.out        = ""

    def is_installed(self):
        return self.is_installed()

    def install(self):
        return self.install()

    def uninstall(self):
        return self.uninstall()


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
