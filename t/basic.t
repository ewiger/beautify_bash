use Test::More tests => 4;

BEGIN {
    if (!eval q{ use Test::Differences; 1 }) {
        *eq_or_diff = \&is_deeply;
    }
}

delete $ENV{PATH};

sub a {
return scalar `/usr/bin/env python ./beautify_bash.py -t3 <<"EOM"
$_[0]
EOM`
}

eq_or_diff a(<<'EOM'), <<'EOM', 'If then else';
echo            
if [ $? -eq 0 ]     
   then     
         echo   
               else     
                  echo     
                        fi   
EOM
echo
if [ $? -eq 0 ]
then
   echo
else
   echo
fi

EOM

eq_or_diff a(<<'EOM'), <<'EOM', 'If then else, in func staircase';
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

eq_or_diff a(<<'EOM'), <<'EOM', 'If then else, in func';
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

eq_or_diff a(<<'EOM'), <<'EOM', 'If then else, in func, if/then oneline';
            func()
                     {
echo
if [ $? -eq 0 ]; then echo
               else
                  echo
                        fi
                }
EOM
func()
{
   echo
   if [ $? -eq 0 ]; then echo
   else
      echo
   fi
}

EOM

