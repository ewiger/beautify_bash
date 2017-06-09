#!/bin/bash

CASES=1

describe()
{
   echo "trim lines with empty spaces"
}

input1()
{
   cat <<"EOM"
            func() {
    echo
                          
        echo
                }
EOM
}

expected1()
{
   cat <<"EOM"
func() {
   echo

   echo
}
EOM
}
