#!/bin/bash

CASES=4

describe()
{
   echo "Basic if then else"
}

input1()
{
   cat <<"EOM"
echo            
if [ $? -eq 0 ]     
   then     
         echo   
               else     
                  echo     
                        fi   
EOM
}

expected1()
{
   cat <<"EOM"
echo
if [ $? -eq 0 ]
then
   echo
else
   echo
fi
EOM
}

input2()
{
   cat <<"EOM"
                              func() {     
echo     
if [ $? -eq 0 ]     
   then     
         echo     
               else     
                  echo     
                        fi     
                }     
EOM
}

expected2()
{
   cat <<"EOM"
func() {
   echo
   if [ $? -eq 0 ]
   then
      echo
   else
      echo
   fi
}
EOM
}

input3()
{
   cat <<"EOM"
            func()
                     {
echo
if [ $? -eq 0 ]
   then
echo
               else
                  echo
                        fi
                }
EOM
}

expected3()
{
   cat <<"EOM"
func()
{
   echo
   if [ $? -eq 0 ]
   then
      echo
   else
      echo
   fi
}
EOM
}

input4()
{
   cat <<"EOM"
            func()
                     {
echo
if [ $? -eq 0 ]; then echo
               else
                  echo
                        fi
                }
EOM
}

expected4()
{
   cat <<"EOM"
func()
{
   echo
   if [ $? -eq 0 ]; then echo
   else
      echo
   fi
}
EOM
}
