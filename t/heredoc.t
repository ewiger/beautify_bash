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

eq_or_diff a(<<'EOM'), <<'EOM', 'Here doc';
                  cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
EOM
cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
then
   :
fi

EOM

eq_or_diff a(<<'EOM'), <<'EOM', 'Here doc';
                  cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
EOM
cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
then
   :
fi

EOM

eq_or_diff a(<<'EOM'), <<'EOM', 'Here doc';
                  func() {
                  cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
                     }
EOM
func() {
   cat <<"HEHE"
                     if [
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
   if [ $? -eq 0 ]
   then
      :
   fi
}

EOM

eq_or_diff a(<<'EOM'), <<'EOM', 'Here doc';
                  func() {
                  cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
if [ $? -eq 0 ]
   then
   :
                        fi
                     }
EOM
func() {
   cat <<HEHE
                     if [ $x
                        then

HEHEFOOLER
   HEHE
                     if [ $? -eq 1 ]
                        then
HEHE
   if [ $? -eq 0 ]
   then
      :
   fi
}

EOM
