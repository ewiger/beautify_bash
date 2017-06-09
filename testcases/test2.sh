#!/bin/bash

CASES=4

describe()
{
   echo "here docs"
}

input1()
{
   cat <<"EOM"
                  cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
EOM
}

expected1()
{
   cat <<"EOM"
cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
then
   :
fi
EOM
}

input2()
{
   cat <<"EOM"
                  cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
EOM
}

expected2()
{
   cat <<"EOM"
cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
then
   :
fi
EOM
}

input3()
{
   cat <<"EOM"
                  func() {
                  cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
                     }
EOM
}

expected3()
{
   cat <<"EOM"
func() {
   cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
   if [ $? -eq 0 ]
   then
      :
   fi
}
EOM
}

input4()
{
   cat <<"EOM"
                  func() {
                  cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
                     }
EOM
}

expected4()
{
   cat <<"EOM"
func() {
   cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
   if [ $? -eq 0 ]
   then
      :
   fi
}
EOM
}
