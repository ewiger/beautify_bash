#!/bin/bash

CASES=2

describe()
{
   echo "string literals"
}

input1()
{
   cat <<"EOM"
func() {
                X1="This is a 'test' about quotes"   
          X2='This is a "test" about quotes'     
             Y1="This          
               is a 'te   
               quotes"  
            Y2='This   
               is a "te   
               quotes'   
             Y3="This          
               is a \"te   
               quotes"  
            echo
}
EOM
}

expected1()
{
   cat <<"EOM"
func() {
   X1="This is a 'test' about quotes"
   X2='This is a "test" about quotes'
   Y1="This          
               is a 'te   
               quotes"
   Y2='This   
               is a "te   
               quotes'
   Y3="This          
               is a \"te   
               quotes"
   echo
}
EOM
}

input2()
{
   cat <<"EOM"
func() {
             Y1="This          
                this is <<HERE  
               quotes"   
               echo
}
EOM
}

expected2()
{
   cat <<"EOM"
func() {
   Y1="This          
                this is <<HERE  
               quotes"
   echo
}
EOM
}
