use Test::More tests => 2;

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

eq_or_diff a(<<'EOM'), <<'EOM', 'Split long lines';
func() {
   if [ $? -eq 0 ]; then if [ $? -eq 0 ]; then if [ $? -eq 0 ]; then echo; else; echo; fi; else; echo; fi; else; echo; fi
}
EOM
func() {
   if [ $? -eq 0 ]; then if [ $? -eq 0 ]; then
         if [ $? -eq 0 ]; then echo; else; echo; fi; else; echo; fi
   else; echo; fi
}

EOM

eq_or_diff a(<<'EOM'), <<'EOM', 'Join short lines';
func() {
   if [ $? -eq 0 ] &&
      [ $? -eq 0 ] ||
      [ $? -eq 0 ]; then
      echo
   else
     echo
   fi
}
EOM
func() {
   if [ $? -eq 0 ] && [ $? -eq 0 ] || [ $? -eq 0 ]; then
      echo
   else
     echo
   fi
}

EOM
