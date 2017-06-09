#!/bin/bash

CASES=1

describe()
{
   echo "elif"
}

input1()
{
   cat <<"EOM"
if [ $? -eq 0 ]
then
   :
   elif [ $? -ne 0 ]
      then
         :
fi
EOM
}

expected1()
{
   cat <<"EOM"
if [ $? -eq 0 ]
then
   :
elif [ $? -ne 0 ]
then
   :
fi
EOM
}
