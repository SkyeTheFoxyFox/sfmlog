from util import *
from parse import parser
import copy

class macros:
	class macro:
		def __init__(self, code):
			self.code = code
			self.inc = 0

		def __repr__(self):
			return(parser.to_string(self.code))

	def find_macros(tokens, macro_list):
		out_code = []
		code = tokens.copy()
		while True:
			try:
				token = code.pop(0)
			except IndexError:
				break
			if(token == parser.instruction and token.value == "defmac"):
				name = code.pop(0)
				if(name != parser.variable):
					ERROR("Invalid name for macro", name.line_number, name.file)
				macro_args = []
				expand_arg = None
				has_ended = False
				arg = code.pop(0)
				while(arg != parser.line_break):
					if(arg != parser.variable):
						ERROR("Invalid macro argument name", arg.line_number, arg.file)
					if has_ended:
						ERROR(f"Unexpected arguments after '{expand_arg}...'", arg.line_number, arg.file)
					if arg.value.endswith("..."):
						expand_arg = arg.value[:-3]
						macro_args.append(expand_arg)
						has_ended = True
					else:
						macro_args.append(arg.value)
					arg = code.pop(0)

				macro_code = []
				macro_token = code.pop(0)
				while(not(macro_token == parser.instruction and macro_token.value == "endmac")):
					if(macro_token == parser.instruction and macro_token.value == "defmac"):
						ERROR("Can't define a macro within a macro", macro_token.line_number, macro_token.file)
					#elif(macro_token == parser.instruction and macro_token.value == "deffun"):
					#	ERROR("Can't define a macro within a function", macro_token.line_number, macro_token.file)

					elif macro_token == parser.variable and macro_token.value == expand_arg:
						macro_code.append(parser.macro_expand(macro_args.index(macro_token.value)))
						macro_code[-1].set_line_number(macro_token.line_number)
						macro_code[-1].set_file(macro_token.file)
					elif(macro_token == parser.variable and macro_token.value in macro_args):
						macro_code.append(parser.macro_variable(macro_args.index(macro_token.value)))
						macro_code[-1].set_line_number(macro_token.line_number)
						macro_code[-1].set_file(macro_token.file)
					else:
						macro_code.append(macro_token)
					try:
						macro_token = code.pop(0)
					except IndexError:
						ERROR("Macro definition not closed", name.line_number, name.file)
				consume = None
				while(consume != parser.line_break):
					consume = code.pop(0)
				macro_list[name.value] = macros.macro(macro_code)

			else:
				out_code.append(token)
		return(out_code)

	def expand_macros(tokens, macro_list):
		out_code = []
		code = tokens.copy()
		while True:
			try:
				token = code.pop(0)
			except IndexError:
				break
			if(token == parser.instruction and token.value == "mac"):
				mac_name = code.pop(0)
				if(mac_name != parser.variable or mac_name.value not in macro_list):
					ERROR("Unknown macro", mac_name.line_number, mac_name.file)
				macro_args = []
				arg = code.pop(0)
				while(arg != parser.line_break):
					#if arg == parser.composite_variable:
					#	macro_args.append(arg.collapse_var(arg_list = args))
					#else:
					macro_args.append(arg)
					arg = code.pop(0)

				macro_called_list = []

				expand_macro(out_code, macro_list[mac_name.value], mac_name.value, macro_args, macro_list, macro_called_list.copy())

			else:
				out_code.append(token)
		return(out_code)

	def flush_scope(tokens):
		for token in tokens:
			if(token in [parser.variable, parser.composite_variable, parser.label]):
				token.flush_scope()

def expand_macro(out_code, macro, macro_name, args, macro_list, macro_called_list):
	macro_called_list.append(macro_name)
	macro_called = False
	code = copy.deepcopy(macro.code)
	while True:
		try:
			mac_token = code.pop(0)
		except IndexError:
			break
		if(mac_token == parser.instruction and mac_token.value == "mac"):
			mac_name = code.pop(0)
			#print(mac_name)
			if mac_name == parser.macro_variable:
				try:
					mac_name = args[mac_name.value]
				except IndexError:
					ERROR("Failed to expand argument as macro name, as it is undefined", mac_name.line_number, mac_name.file)
			if(mac_name != parser.variable or mac_name.value not in macro_list):
				ERROR("Unknown macro", mac_name.line_number, mac_name.file)
			if(mac_name.value in macro_called_list):
				ERROR("Can't call macro within itself", mac_name.line_number, mac_name.file)
			macro_args = []
			arg = code.pop(0)
			while(arg != parser.line_break):
				if arg == parser.macro_expand:
					if arg.value < len(args):
						macro_args.extend(args[arg.value:])
					else:
						macro_args.append(parser.defined_literal("null"))
				elif arg == parser.macro_variable:
					try:
						macro_args.append(args[arg.value])
					except IndexError:
						macro_args.append(parser.defined_literal("null"))
				elif(arg == parser.composite_variable):
					#macro_args.append(arg.collapse_var())
					macro_args.append(arg)
				elif(arg in [parser.variable, parser.label]):
					macro_args.append(arg)
					macro_args[-1].set_scope(f"_{macro_name}_{macro.inc}_")
				else:
					macro_args.append(arg)
				arg = code.pop(0)

			

			expand_macro(out_code, macro_list[mac_name.value], mac_name.value, macro_args, macro_list, macro_called_list.copy())
		elif(mac_token == parser.macro_variable):
			try:
				out_code.append(args[mac_token.value])
			except IndexError:
				out_code.append(parser.defined_literal("null"))
			out_code[-1].set_line_number(mac_token.line_number)
			out_code[-1].set_file(mac_token.file)
		elif mac_token == parser.macro_expand:
			if mac_token.value < len(args):
				out_code.extend(args[mac_token.value:])
			else:
				out_code.append(parser.defined_literal("null"))
			out_code[-1].set_line_number(mac_token.line_number)
			out_code[-1].set_file(mac_token.file)
		elif(mac_token in [parser.variable, parser.composite_variable, parser.label]):
			out_code.append(mac_token)
			out_code[-1].set_scope(f"_{macro_name}_{macro.inc}_")
			macro_called = True
		else:
			out_code.append(mac_token)
	if(macro_called):
		macro.inc += 1