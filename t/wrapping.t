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

eq_or_diff a(<<'EOM'), <<'EOM', 'lines ending with \\, &&, |, ||';
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
