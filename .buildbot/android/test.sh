#!/bin/bash

release_artifact=$(grep release_artifact packages/android/buildozer.spec |cut -d= -f2|tr -Cd 'a-z')

if [ $release_artifact = "aab" ]; then
	exit
fi

unzip -p packages/android/bin/*.apk assets/private.tar \
    | tar --list -z > package.list
cat package.list
cat package.list | grep '\.sql$' || exit 1
