#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
#from hypchat.__main__ import hipchat

DOCUMENTATION = '''
---
module: hipchat_chat
version_added: "1.8"
short_description: Create, delete or configure a HipChat room
description:
   - Create, delete or configure a HipChat room
options:
  token:
    description:
      - API token.
    required: true
  room:
    description:
      - ID or name of the room. Max. 50 characters
    required: true
  state:
    description:
      - Whether to create (present) or remove (absent) a room
    required: true
    default: present
  topic:
    description:
      - The topic for the room
    required: false
    default: null
  guest_access:
    description:
      - Whether or not to enable guest access for the room
    required: false
    default: no
    choices: [ "yes", "no" ]
  owner_user_id:
    description:
      - The id, email address or mention name (beginning with an '@') of the room
s owneer. Defaults to API token owner.
    required: false
    default: null
    choices: [ "text", "html" ]
  privacy:
    description:
      - Whether the room is avalable for access by other users or not
    required: false
    default: "public"
    choices: [ "public", "private" ]
  api:
    description:
      - API url if using a self-hosted hipchat server
    required: false
    default: "https://api.hipchat.com/"
  api_version:
    description:
      - API version
    required: false
    default: "2"


# informational: requirements for nodes
requirements: [ urllib, urllib2 ]
author: Rob White
'''

EXAMPLES = '''
- hipchat_room: token=AAAAA room=myroom state=present
'''

# ===========================================
# HipChat module specific support methods.
#
import httplib2

class HipchatRoom(object):
    
    def __init__(self, module):
        self.module = module
        self.changed = False
        self.token = module.params["token"]
        self.room = module.params["room"]
        self.state = module.params["state"]
        self.topic = module.params["topic"]
        self.guest_access = module.params["guest_access"]
        self.owner_user_id = module.params["owner_user_id"]
        self.privacy = module.params["privacy"]
        self.api = module.params["api"]
        self.api_version = module.params["api_version"]
        self.err        = ""
        self.out        = ""
        
        if self.api_version == "1":
            self.url_headers = {'content-type': 'application/x-www-form-urlencoded'}
        elif self.api_version == "2":
            self.url_headers = {'content-type': 'application/json', 'authorization': 'Bearer %s' % self.token}

    def get_room(self):

        url = self.api + "v2/room/" + self.room
        
        response, content, dest = self.uri(url, None, None, None, "", "GET", self.url_headers, "yes", 30)
        
        if response.get("status") == "200":
            return json.loads(content)
        elif response.get("status") == "404":
            json_content = json.loads(content)
            if json_content['error']['message'] == "Room not found":
                return None
        else:
            json_content = json.loads(content)
            module.fail_json(msg=json_content['error']['message'])
            
    
    def get_room_list(self):
        
        if self.api_version == "1":
            # Construct url
            url = self.api + "v1/rooms/list?format=json"
            response, content, dest = self.uri(url, None, None, None, "", "GET", self.url_headers, "yes", 30)
        elif self.api_version == "2":
            url = self.api + "v2/room?include-private=false"
            response, content, dest = self.uri(url, None, None, None, "", "GET", self.url_headers, "yes", 30)
            
        if response.get("status") == "200":
            return json.loads(content)
        else:
            json_content = json.loads(content)
            module.fail_json(msg=json_content['error']['message'])
            
    def create_room(self):
        
        url = self.api + "v2/room"
        #body = { "topic": self.topic, "guest_access": self.guest_access, "name": self.room, "owner_user_id": self.owner_user_id, "privacy": self.privacy }
        body = { "topic": self.topic, "guest_access": self.guest_access, "name": self.room, "privacy": self.privacy }
        body_json = json.dumps(body)
        response, content, dest = self.uri(url, None, None, None, body_json, "POST", self.url_headers, "yes", 30)
        
        if response.get("status") == "201":
            self.changed = True
            self.out = json.loads(content)
        else:
            json_content = json.loads(content)
            self.module.fail_json(msg=json_content['error']['message'])
            
    def delete_room(self):
        
        url = self.api + "v2/room/" + self.room
        response, content, dest = self.uri(url, None, None, None, "", "DELETE", self.url_headers, "yes", 30)
        
        if response.get("status") == "200":
            self.changed = True
            self.out = content
        else:
            json_content = json.loads(content)
            self.module.fail_json(msg=json_content['error']['message'])
            
    def change_room(self):
        
        return True
    
    
    def compare_room(self, remote_room):
        
        print remote_room['name']
            
            
    # uri - copied straight from ansible uri core module        
    def uri(module, url, dest, user, password, body, method, headers, redirects, socket_timeout):
        # To debug
        #httplib2.debug = 4
    
        # Handle Redirects         
        if redirects == "all" or redirects == "yes":
            follow_redirects = True
            follow_all_redirects = True
        elif redirects == "none":
            follow_redirects = False
            follow_all_redirects = False
        else:
            follow_redirects = True
            follow_all_redirects = False
    
        # Create a Http object and set some default options.
        h = httplib2.Http(disable_ssl_certificate_validation=True, timeout=socket_timeout)
        h.follow_all_redirects = follow_all_redirects
        h.follow_redirects = follow_redirects
        h.forward_authorization_headers = True
    
        # If they have a username or password verify they have both, then add them to the request
        if user is not None and password is None:
            module.fail_json(msg="Both a username and password need to be set.")
        if password is not None and user is None:
            module.fail_json(msg="Both a username and password need to be set.")
        if user is not None and password is not None:
            h.add_credentials(user, password)
    
        # is dest is set and is a directory, let's check if we get redirected and
        # set the filename from that url
        redirected = False
        resp_redir = {}
        r = {}
        if dest is not None:
            dest = os.path.expanduser(dest)
            if os.path.isdir(dest):
                # first check if we are redirected to a file download
                h.follow_redirects=False
                # Try the request
                try:
                    resp_redir, content_redir = h.request(url, method=method, body=body, headers=headers)
                    # if we are redirected, update the url with the location header,
                    # and update dest with the new url filename
                except:
                    pass
                if 'status' in resp_redir and resp_redir['status'] in ["301", "302", "303", "307"]:
                    url = resp_redir['location']
                    redirected = True
                dest = os.path.join(dest, url_filename(url))
            # if destination file already exist, only download if file newer
            if os.path.exists(dest):
                t = datetime.datetime.utcfromtimestamp(os.path.getmtime(dest))
                tstamp = t.strftime('%a, %d %b %Y %H:%M:%S +0000')
                headers['If-Modified-Since'] = tstamp
    
        # do safe redirects now, including 307
        h.follow_redirects=follow_redirects
    
        # Make the request, or try to :)
        try: 
            resp, content = h.request(url, method=method, body=body, headers=headers)     
            r['redirected'] = redirected
            r.update(resp_redir)
            r.update(resp)
            try:
                return r, unicode(content.decode('unicode_escape')), dest
            except:
                return r, content, dest
        except httplib2.RedirectMissingLocation:
            self.module.fail_json(msg="A 3xx redirect response code was provided but no Location: header was provided to point to the new location.")
        except httplib2.RedirectLimit:
            self.module.fail_json(msg="The maximum number of redirections was reached without coming to a final URI.")
        except httplib2.ServerNotFoundError:
            self.module.fail_json(msg="Unable to resolve the host name given.")
        except httplib2.RelativeURIError:
            self.module.fail_json(msg="A relative, as opposed to an absolute URI, was passed in.")
        except httplib2.FailedToDecompressContent:
            self.module.fail_json(msg="The headers claimed that the content of the response was compressed but the decompression algorithm applied to the content failed.")
        except httplib2.UnimplementedDigestAuthOptionError:
            self.module.fail_json(msg="The server requested a type of Digest authentication that we are unfamiliar with.")
        except httplib2.UnimplementedHmacDigestAuthOptionError:
            self.module.fail_json(msg="The server requested a type of HMACDigest authentication that we are unfamiliar with.")
        except httplib2.UnimplementedHmacDigestAuthOptionError:
            self.module.fail_json(msg="The server requested a type of HMACDigest authentication that we are unfamiliar with.")
        except socket.error, e:
            self.module.fail_json(msg="Socket error: %s to %s" % (e, url))


# ===========================================
# Module execution.
#

MSG_URI = "https://api.hipchat.com/"

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True),
            room=dict(required=True),
            state=dict(default="present", choices=["present", "absent"]),
            topic=dict(default=""),
            guest_access=dict(default="no", type='bool'),
            owner_user_id=dict(default=""),
            privacy=dict(default="public", choices=["public", "private"]),
            api=dict(default=MSG_URI),
            api_version=dict(default="2", choices=["1", "2"])
        ),
        supports_check_mode=True
    )

    token = module.params["token"]
    room = module.params["room"]
    state = module.params["state"]
    topic = module.params["topic"]
    guest_access = module.params["guest_access"]
    owner_user_id = module.params["owner_user_id"]
    privacy = module.params["privacy"]
    api = module.params["api"]
    api_version = module.params["api_version"]

    hipchat_room = HipchatRoom(module)
    result = {}
    result['changed'] = False
    
    try:
        if hipchat_room.state == "present":
            room_remote = hipchat_room.get_room()
            if room_remote is not None:
                if hipchat_room.compare_room(room_remote):
                    hipchat_room.change_room()
            else:
                hipchat_room.create_room()
        
        if hipchat_room.state == "absent":
            if hipchat_room.get_room() is not None:
                hipchat_room.delete_room()
                
        result['changed'] = hipchat_room.changed
        result['out'] = hipchat_room.out
        result['err'] = hipchat_room.err

        module.exit_json(**result)
        
    except RuntimeError as e:
        module.fail_json(msg=str(e))
    except EnvironmentError as e:
        module.fail_json(msg=str(e))


#room_result = create_room(module, token, api, api_version, room, topic, guest_access, owner_user_id, privacy)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
