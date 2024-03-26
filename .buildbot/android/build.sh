#!/bin/bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
pushd packages/android
buildozer android release || exit $?
popd

mkdir -p ../out
release_artifact=$(grep release_artifact packages/android/buildozer.spec |cut -d= -f2|tr -Cd 'a-z')
cp packages/android/bin/*.${release_artifact} ../out
