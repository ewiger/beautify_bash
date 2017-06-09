#!/bin/bash

CASES=1

describe()
{
   echo "line wrapping when ending with \\, &&, |, ||"
}

input1()
{
   cat <<"EOM"
func() {
                echo alpha \
          beta \
             gamma \
               delata
            echo
                echo a |
                  grep x |
          grep y |
            grep z |
               grep p
            echo
                echo a &&
                  grep x &&
          grep y &&
            grep z &&
               grep p
                echo
                echo a ||
                  grep x ||
          grep y ||
            grep z ||
               grep p
                 echo
}
EOM
}

expected1()
{
   cat <<"EOM"
func() {
   echo alpha \
      beta \
      gamma \
      delata
   echo
   echo a |
      grep x |
      grep y |
      grep z |
      grep p
   echo
   echo a &&
      grep x &&
      grep y &&
      grep z &&
      grep p
   echo
   echo a ||
      grep x ||
      grep y ||
      grep z ||
      grep p
   echo
}
EOM
}
