from util import *

from arguments import arguments
from parse import parser 
from imports import imports
from const import consts
from macro import macros
from pre_exec import pre_exec

import re, sys, pyperclip

args = arguments(sys.argv)

code = parser.from_file(args.input_file)

code = imports.handle_imports(code)

const_list = {}
code = consts.find_consts(code, const_list)
code = consts.expand_consts(code, const_list)

macro_list = {}
code = macros.find_macros(code, macro_list)
#print(macro_list)
code = macros.expand_macros(code, macro_list)

macros.flush_scope(code)

code = pre_exec.evaluate_code(code)

if(args.copy):
	pyperclip.copy(parser.to_string(code))
if(args.output_file != ""):
	with open(args.output_file, "w") as file:
		file.write(parser.to_string(code))
		file.close()
if args.stdout:
	print(parser.to_string(code))
else:
	print("done")

#print(parser.to_string(code))
