#!/bin/bash

ALL_TESTS=( $(echo ./testcases/*.sh) )
TOTAL_TESTS=${#ALL_TESTS[@]};
PASSED=0
FAILED=0

for (( i = 0 ; i < $TOTAL_TESTS; ++i ))
do
   test_file=${ALL_TESTS[$i]}
   test_name="$(basename $test_file)"

   e=0;
   (
      CASES=1
      source $test_file

      echo "============================================================="
      echo "TEST $test_name ($((i+1)) of $TOTAL_TESTS): $(describe)"
      echo

      chr=' '
      e=0;
      for (( cc = 1 ; cc <= $CASES ; ++cc ))
      do
         echo "   CASE $cc of $CASES:"
         echo "   -------------------------------------------------------------"
         echo "   inp:"
         input$cc | tee /tmp/input.txt | sed -e 's/^/   /' | sed -e "s/ /$chr/g"
         echo "   -------------------------------------------------------------"

         (
            e=0;
            echo "   got:                                                            exp:"
            diff -y <(input$cc | python ./beautify_bash.py -t3 - | sed -e "s/ /$chr/g" | sed -e 's/^/   /') <(expected$cc | sed -e "s/ /$chr/g" | sed -e 's/^/   /') || e=1

            status=PASS && [ $e -ne 0 ] && status=FAIL
            echo "   -------------------------------------------------------------"
            echo "   CASE $cc of $CASES - $status"
            echo
            exit $e;
         ) || ((++e))
      done

      exit $e;
   ) || ((++e))

   [ $e -eq 0 ] && (( PASSED++ ))
   [ $e -ne 0 ] && (( FAILED++ ))

   status=PASS && [ $e -ne 0 ] && status=FAIL
   echo
   echo "TEST $test_name ($((i+1)) of $TOTAL_TESTS): $status"
   echo "============================================================="
done

echo "============================================================="
echo "TEST SUMMARY : PASSED: $PASSED, FAILED: $FAILED"
echo "============================================================="
