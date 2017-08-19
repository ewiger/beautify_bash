use Test::More tests => 1;

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

eq_or_diff a(<<'EOM'), <<'EOM', 'elif';
if [ $? -eq 0 ]
then
   :
   elif [ $? -ne 0 ]
      then
         :
fi
EOM
if [ $? -eq 0 ]
then
   :
elif [ $? -ne 0 ]
then
   :
fi

EOM
