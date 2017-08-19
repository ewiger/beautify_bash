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

eq_or_diff a(<<'EOM'), <<'EOM', 'String literals';
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

eq_or_diff a(<<'EOM'), <<'EOM', 'String literals, fake here doc';
func() {
             Y1="This          
                this is <<HERE  
               quotes"   
               echo
}
EOM
func() {
   Y1="This          
                this is <<HERE  
               quotes"
   echo
}

EOM
