#!/usr/bin/python
# -*- coding: utf-8 -*-

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_computername
version_added: "1.7"
short_description: Manages local Windows computer name
description:
     - Manages local Windows computer name. 
     - A reboot is required for the computer name to take effect
options:
  name:
    description:
      - Name of the computer
    required: true
    default: null
    aliases: []
author: Rob White
'''

EXAMPLES = '''
# Ad-hoc example
- win_computername: name=web01
'''
