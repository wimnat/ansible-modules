#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64

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

MSG_URI = "https://api.hipchat.com/"

def get_all_rooms(module, token, api, api_version):
    
    params = {}
    params['api'] = api
    params['api_version'] = api_version
    params['token'] = token

    if api_version == "1":
        url = api + "v1/rooms/list?format=json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
    elif api_version == "2":
        url = api + "v2/room?include-private=false"
        headers = {'content-type': 'application/json'}

    url += "&auth_token=%s" % (token)

    response, info = fetch_url(module, url, headers=headers)

    if info['status'] == 200:
        return response.read()
    else:
        module.fail_json(msg="failed to get all rooms, return status=%s" % str(info['status']))

def check_room_exists(room_list, room):
    json_obj = json.loads(room_list)
    for r in json_obj['items']:
        if r['name'] == room:
            return r
    return None

def create_room(module, token, api, api_version, room, topic, guest_access, owner_user_id, privacy):
    
    params = {}
    params['room'] = room
    if topic is not None:
        params['topic'] = topic
    params['guest_access'] = guest_access
    if owner_user_id is not None:
        params['owner_user_id'] = owner_user_id
    params['privacy'] = privacy
    #params['auth_token'] = token

    if api_version == "1":
        url = api + "v1/rooms/list?format=json"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
    elif api_version == "2":
        url = api + "v2/room"
        base64string = base64.encodestring('%s' % (token))
        headers = {'content-type': 'application/json', 'authorization': 'Bearer %s' % base64string}
    
    #url += "?auth_token=%s" % (token)

    data = urllib.urlencode(params)

    response, info = fetch_url(module, url, data=data, headers=headers)
 
    if info['status'] == 200:
        return response.read()
    else:
        module.fail_json(msg="failed to create room, return status=%s" % str(info['status']))


def send_msg(module, token, room, msg_from, msg, msg_format='text',
             color='yellow', notify=False, api=MSG_URI):
    '''sending message to hipchat'''

    params = {}
    params['room_id'] = room
    params['from'] = msg_from[:15]  # max length is 15
    params['message'] = msg
    params['message_format'] = msg_format
    params['color'] = color
    params['api'] = api

    if notify:
        params['notify'] = 1
    else:
        params['notify'] = 0

    url = api + "?auth_token=%s" % (token)
    data = urllib.urlencode(params)
    response, info = fetch_url(module, url, data=data)
    if info['status'] == 200:
        return response.read()
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True),
            room=dict(required=True),
            state=dict(default="present", choices=["present", "absent"]),
            topic=dict(default=None),
            guest_access=dict(default="no", type='bool'),
            owner_user_id=dict(default=None),
            privacy=dict(default="public", choices=["public", "private"]),
            api=dict(default=MSG_URI),
            api_version=dict(default="1", choices=["1", "2"])
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

    #try:
    room_list = get_all_rooms(module, token, api, api_version)
    if state == "present":
        if check_room_exists(room_list, room) is not None:
            # See if room needs to be changed
            msg = "Room exists"
            changed = False
        else:
            # Create the room
            room_result = create_room(module, token, api, api_version, room, topic, guest_access, owner_user_id, privacy)
            print room_result
            msg = "Room created"
            changed = True
    #except Exception, e:
    #    module.fail_json(msg="unable to sent msg: %s" % e)

    module.exit_json(changed=changed, msg=msg) #, msg_from=msg_from, msg=msg)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
