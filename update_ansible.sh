#!/bin/bash

repo=$1

if [ "$repo" != "core" ] && [  "$repo" != "extras" ]; then
   echo "Should be core or extras"
   exit 1
fi

git remote add upstream git@github.com:ansible/ansible-modules-${repo}.git
git fetch upstream
git checkout devel
git merge upstream/devel
git push
