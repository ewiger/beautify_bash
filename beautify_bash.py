#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************
#   Copyright (C) 2011, Paul Lutus                                        *
#                                                                         *
#   This program is free software; you can redistribute it and/or modify  *
#   it under the terms of the GNU General Public License as published by  *
#   the Free Software Foundation; either version 2 of the License, or     *
#   (at your option) any later version.                                   *
#                                                                         *
#   This program is distributed in the hope that it will be useful,       *
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#   GNU General Public License for more details.                          *
#                                                                         *
#   You should have received a copy of the GNU General Public License     *
#   along with this program; if not, write to the                         *
#   Free Software Foundation, Inc.,                                       *
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
#**************************************************************************

import re
import sys
import getopt

PVERSION = '1.0'


class BeautifyBash:

    def __init__(self):
        self.tab_str = ' '
        self.tab_size = 2

    def read_file(self, fp):
        with open(fp) as f:
            return f.read()

    def write_file(self, fp, data):
        with open(fp, 'w') as f:
            f.write(data)

    def beautify_string(self, data, path=''):
        tab = 0
        wrap_tab = ""
        case_stack = []
        ext_quote_string = ''
        here_string = ''
        output = []
        line = 1
        for record in re.split('\n', data):
            test_record = stripped_record = record.strip()
            # strip out any escaped single characters
            test_record = re.sub(r'\\.', '', test_record)
            # remove '#' comments
            test_record = re.sub(r'(\A|\s)(#.*)', '', test_record, 1)
            # collapse multiple quotes between ' ... '
            test_record = re.sub(r'\'.*?\'', '', test_record)
            # collapse multiple quotes between " ... "
            test_record = re.sub(r'".*?"', '', test_record)
            # collapse multiple quotes between ` ... `
            test_record = re.sub(r'`.*?`', '', test_record)
            # collapse multiple quotes between \` ... ' (weird case)
            test_record = re.sub(r'\\`.*?\'', '', test_record)

            if(here_string):  # pass on with no changes
                # now test for here-doc termination string
                if(record == here_string):
                    here_string = ''
                output.append(record)
                continue

            if(ext_quote_string):
                if(re.search(ext_quote_string, test_record)):
                    # provide line after quotes
                    test_record = re.sub('.*%s(.*)' % ext_quote_string, '\\1', test_record, 1)
                    ext_quote_string = ''
                    # pass on left side unchanged
                    output.append(record.rstrip())
                else:
                    # pass on unchanged
                    output.append(record)
                continue

            if(re.search(r'[\'"]', test_record)):
                # apply only after this line has been processed
                ext_quote_string = re.sub('[^\'"]*([\'"]).*', '\\1', test_record, 1)
                # provide line before quote
                test_record = re.sub('(.*)%s.*' % ext_quote_string, '\\1', test_record, 1)
                stripped_record = record.lstrip()

            inc = len(re.findall('(\s|\A|;)(case|then|do)(;|\Z|\s)', test_record))
            inc += len(re.findall('(\{|\(|\[)', test_record))
            outc = len(re.findall('(\s|\A|;)(esac|fi|done|elif)(;|\)|\||\Z|\s)', test_record))
            outc += len(re.findall('(\}|\)|\])', test_record))

            if(re.search(r'\besac\b', test_record)):
                if(len(case_stack) == 0):
                    sys.stderr.write('File %s: error: "esac" before "case" in line %d.\n' % (path, line))
                else:
                    outc += case_stack.pop()

            # sepcial handling for bad syntax within case ... esac
            if(len(case_stack) > 0):
                if(re.search('\A[^(]*\)', test_record)):
                    # avoid overcount
                    outc -= 2
                    case_stack[-1] += 1
                if(re.search(';;', test_record)):
                    outc += 1
                    case_stack[-1] -= 1

            # an ad-hoc solution for the "else" keyword
            else_case = (0, -1)[re.search('^(else)', test_record) is not None]

            net = inc - outc
            tab += min(net, 0)
            extab = tab + else_case
            extab = max(0, extab)
            tab += max(net, 0)

            if(re.search(r'^\s*$', stripped_record) and wrap_tab == ""):
                output.append("")
            else:
                output.append((self.tab_str * self.tab_size * extab) + wrap_tab + stripped_record)

            if(re.search(r'\\\s*$', test_record)
                or re.search(r'[&][&]\s*$', test_record)
                or re.search(r'[|]\s*$', test_record)
               ):
                wrap_tab = self.tab_str * self.tab_size
            else:
                wrap_tab = ""

            if(re.search(r'\bcase\b', test_record)):
                case_stack.append(0)
            if(re.search('<<-?', test_record)):
                here_string = re.sub('.*<<-?\s*[\'"]?([\w]+)[\'"]?.*', '\\1', record.strip(), 1)

            line += 1
        error = (tab != 0)
        if(error):
            sys.stderr.write('File %s: error: indent/outdent mismatch: %d.\n' % (path, tab))
        return '\n'.join(output), error

    def beautify_file(self, path):
        error = False
        if(path == '-'):
            data = sys.stdin.read()
            result, error = self.beautify_string(data, '(stdin)')
            sys.stdout.write(result)
        else:  # named file
            data = self.read_file(path)
            result, error = self.beautify_string(data, path)
            if(data != result):
                # make a backup copy
                self.write_file(path + '~', data)
                self.write_file(path, result)
        return error

    def usage_ex(self, err_val):
        sys.stderr.write('Usage: ' + sys.argv[0] + ' [-h|-t <n>] [<file-name>|-]...\n')
        sys.exit(err_val)

    def main(self):
        try:
            opts, paths = getopt.getopt(sys.argv[1:], "ht:", "help")
        except getopt.GetoptError as err:
            print(err)
            self.usage_ex(2)

        for o, v in opts:
            if o == '-t':
                self.tab_size = int(v)
            elif o in ('-h', '--help'):
                self.usage_ex(0)

        if(len(paths) < 1):
            paths.append('-')

        error = False
        for path in paths:
            error |= self.beautify_file(path)
        sys.exit((0, 1)[error])

# if not called as a module
if(__name__ == '__main__'):
    BeautifyBash().main()
