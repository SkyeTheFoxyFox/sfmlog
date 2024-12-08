from util import *
import re

class parser:
	SUB_INSTRUCTION_MAP = {
		"draw": [True],
		"control": [True],
		"radar": [True, True, True, True],
		"op": [True],
		"lookup": [True],
		"jump": [False, True],
		"ucontrol": [True],
		"uradar": [True, True, True, True],
		"ulocate": [True, True],
		"getblock": [True],
		"setblock": [True],
		"status": [True, True],
		"setrule": [True],
		"message": [True],
		"cutscene": [True],
		"effect": [True],
		"fetch": [True],
		"setmarker": [True],
		"makemarker": [True],
		"pop": [True],
		"spop": [True],
		"if": [True],
		"while": [True]
	}

	LINK_BLOCKS = ["gate", "foundation", "wall", "container", "afflict", "heater", "conveyor", "duct", "press", "tower", "pad", "projector", "swarmer", "factory", "drill", "router", "door", "illuminator", "processor", "sorter", "spectre", "parallax", "cell", "electrolyzer", "display", "chamber", "mixer", "conduit", "distributor", "crucible", "message", "unloader", "refabricator", "switch", "bore", "bank", "accelerator", "disperse", "vault", "point", "nucleus", "panel", "node", "condenser", "smelter", "pump", "generator", "tank", "reactor", "cultivator", "malign", "synthesizer", "deconstructor", "meltdown", "centrifuge", "radar", "driver", "void", "junction", "diffuse", "pulverizer", "salvo", "bridge", "acropolis", "dome", "reconstructor", "separator", "citadel", "concentrator", "mender", "lancer", "source", "loader", "duo", "melter", "crusher", "fabricator", "redirector", "disassembler", "gigantic", "incinerator", "scorch", "battery", "tsunami", "arc", "compressor", "assembler", "smite", "module", "bastion", "segment", "constructor", "ripple", "furnace", "wave", "foreshadow", "link", "mine", "scathe", "canvas", "diode", "extractor", "fuse", "kiln", "sublimate", "scatter", "cyclone", "titan", "turret", "lustre", "thruster", "shard", "weaver", "huge", "breach", "hail"]

	class token:
		NUMERIC = False

		def __repr__(self):
			return("token")

		def set_line_number(self, value: int):
			self.line_number = value

		def set_file(self, file: str):
			self.file = file

		def __eq__(self, test):
			return(self.__class__ == test)

		def __ne__(self, test):
			return(self.__class__ != test)

		def __contains__(self, test):
			return(self.__class__ in test)

	class line_break(token):
		def __init__(self, preserve_line_number: bool):
			self.preserve_line_number = preserve_line_number

		def __repr__(self):
			return("\n")

	class instruction(token): #starts a line, doesn't end with ':'
		def __init__(self, value: str):
			self.value = value #the instruction

		def __repr__(self):
			return(self.value)

	class sub_instruction(token): #follows an assosiated instruction
		def __init__(self, value: str, offset: int):
			self.value = value #the sub-instruction
			self.offset = offset #the offset from the previous instruction

		def __repr__(self):
			return(self.value)

	class variable(token): #isn't anything else
		def __init__(self, value: str):
			self.value = value #the name of the variable
			self.scope = ""
		
		def __repr__(self):
			return(f"{self.scope}{self.value}")

		def set_scope(self, scope: str):
			self.scope = scope

		def flush_scope(self):
			self.value = f"{self.scope}{self.value}"
			self.scope = ""
			
	class composite_variable(token): #contains one or more sets of braces, with their own token inside
		def __init__(self, value: str, line_number: int, file: int):
			self.value = value #the original text
			self.scope = ""

			tokens = []
			temp_str = ""
			self.format_value = ""
			composite_depth = 0
			for char in value:
				if(char == '}'):
					composite_depth -= 1
					if(composite_depth == 0):
						if(temp_str == ""):
							ERROR("Unexpected empty braces", line_number, file)
						tokens.append(temp_str)
						temp_str = ""

				if(composite_depth == 0):
					self.format_value += char
				else:
					temp_str += char

				if(char == '{'):
					composite_depth += 1

			self.tokens = []
			for token in tokens:
				self.tokens.append(parser.parse_token(token, [parser.token()], 0, line_number, file))
		
		def __repr__(self):
			return(f"{self.scope}{self.format_value.format(*self.tokens)}")

		def set_line_number(self, value: int):
			self.line_number = value

			for token in self.tokens:
				token.set_line_number(value)

		def set_file(self, file:str):
			self.file = file

			for token in self.tokens:
				token.set_file(file)

		def set_scope(self, scope: str):
			self.scope = scope

			for token in self.tokens:
				if(token in [parser.variable, parser.composite_variable]):
					token.set_scope(scope)

		def flush_scope(self):
			for token in self.tokens:
				if(token in [parser.variable, parser.composite_variable]):
					token.flush_scope()

		def collapse_vars(self, var_list):
			out_token_list = []
			for token in self.tokens:
				if token == parser.variable and token.value in var_list:
					out_token_list.append(parser.parse_token(var_list[token.format_value], [parser.token()], 0, self.line_number, self.file))
				else:
					out_token_list.append(token)

			out_token = parser.parse_token(self.format_value.format(*out_token_list), [parser.token()], 0, self.line_number, self.file)
			out_token.set_scope(self.scope)

		def replace_vars(self, arg_list):
			out_token_list = []
			for token in self.tokens:
				if(token == parser.macro_variable):
					try:
						out_token_list.append(arg_list[token])
					except IndexError:
						out_token_list.append(parser.defined_literal("null"))
				elif(token == parser.composite_variable):
					out_token_list.append(token.replace_vars(arg_list))
				else:
					out_token_list.append(token)

	class global_variable(token): #begins with '$'
		def __init__(self, value: str):
			self.value = value #the name of the variable

		def __repr__(self):
			return(self.value)

	class macro_variable(token):
		def __init__(self, value: int):
			self.value = value #the index into the macro's arguments that this value refers to

		def __repr__(self):
			return(f"macro_var_{self.value}")

	class macro_expand(token):
		def __init__(self, value: int):
			self.value = value #the index into the macro's arguments that this value refers to

		def __repr__(self):
			return(f"macro_expand_{self.value}")
			
	class label(token): #starts a line, ends with a ':'
		def __init__(self, value: str):
			self.value = value #the name of the label
			self.scope = ""
		
		def __repr__(self):
			return(f"{self.scope}{self.value}")

		def set_scope(self, scope: str):
			self.scope = scope

		def flush_scope(self):
			self.value = f"{self.scope}{self.value}"
			self.scope = ""

	class defined_literal(token): #true, false, null
		def __init__(self, value: str):
			self.value = value #the string
		
		def __repr__(self):
			return(self.value)

	class string_literal(token): #encased by quotes
		def __init__(self, value: str):
			self.value = value #the string
		
		def __repr__(self):
			return( '"' + self.value + '"')
			
	class decimal_literal(token): #a decimal value
		NUMERIC = True

		def __init__(self, value: str):
			self.value = value #the original text
			self.float = float(value) #a parsed float value
		
		def __repr__(self):
			return(self.value)
			
	class hex_literal(token): #a hex value
		NUMERIC = True

		def __init__(self, value: str):
			self.value = value #the original text
			self.float = float(int(value, 16)) #a parsed float value
		
		def __repr__(self):
			return(self.value)
			
	class binary_literal(token): #a binary value
		NUMERIC = True

		def __init__(self, value: str):
			self.value = value #the original text
			self.float = float(int(value, 2)) #a parsed float value
		
		def __repr__(self):
			return(self.value)
			
	class exponent_literal(token): #a value in exponent notation
		NUMERIC = True
		
		def __init__(self, value: str):
			self.value = value #the original text
			self.float = float(value) #a parsed float value

		def __repr__(self):
			return(self.value)

	class color_literal(token): #a color
		def __init__(self, value: str):
			self.value = value

		def __repr__(self):
			return(self.value)
			
	class content_literal(token): #begins with '@'
		def __init__(self, value: str):
			self.value = value #the value

		def __repr__(self):
			return(self.value)
			
	class link_literal(token): #probably a link because it's a block in the game followed by a number
		def __init__(self, value: str):
			self.value = value #the value

		def __repr__(self):
			return(self.value)

	def parse_token(string: str, token_arr: list, last_instruction_index: int, line_number: int, file: str):

		if(token_arr[last_instruction_index] == parser.label):
			ERROR("Unexpected text after label", line_number, file)

		if(string[0] == '"' and string[-1] == '"'):
			return(parser.string_literal(string[1:-1]))

		if(string[0] == '%'):
			return(parser.color_literal(string))

		if(re.search(r"^0x[0-9a-fA-F]*$", string)):
			return(parser.hex_literal(string))

		if(re.search(r"^0b[01]*$", string)):
			return(parser.binary_literal(string))

		if(re.search(r"^-?[0-9]*(\.[0-9]*)?$", string)):
			return(parser.decimal_literal(string))

		if(re.search(r"^-?[0-9]*(\.[0-9]*)?e-?[0-9]*(\.[0-9]*)?$", string)):
			return(parser.exponent_literal(string))

		if(string[0] == '@'):
			return(parser.content_literal(string))

		if((string.rstrip("1234567890") in parser.LINK_BLOCKS) and (string != string.rstrip("1234567890"))):
			return(parser.link_literal(string))

		if(token_arr[-1] == parser.line_break):
			if(string[-1] == ':'):
				return(parser.label(string))
			else:
				return(parser.instruction(string))

		if(token_arr[last_instruction_index] in [parser.label, parser.instruction] and token_arr[last_instruction_index].value in parser.SUB_INSTRUCTION_MAP):
			offset = len(token_arr) - last_instruction_index
			if(offset-1 < len(parser.SUB_INSTRUCTION_MAP[token_arr[last_instruction_index].value]) and parser.SUB_INSTRUCTION_MAP[token_arr[last_instruction_index].value][offset-1]):
				return(parser.sub_instruction(string, offset))

		if('{' in string):
			return(parser.composite_variable(string, line_number, file))

		if(string[0] == '$'):
			return(parser.global_variable(string[1:]))

		if(string in ["true", "false", "null"]):
			return(parser.defined_literal(string))

		return(parser.variable(string))

	def from_string(text: str, file: str):
		trimmed_text = parser.trim_text(text)

		token_arr = [parser.line_break(False)]
		token_arr[0].set_line_number(-1)
		token_arr[0].set_file("")
		temp_str = ""
		prev_char = ""
		last_instruction_index = 0

		line_number = 1

		in_string = False
		was_string = False
		composite_depth = 0
		
		for char in trimmed_text:
			if(was_string == True and prev_char == '"' and char not in " \n;"):
				ERROR("Unexpected text after closing quotation mark", line_number, file)

			if(char == '{'):
				composite_depth += 1
				temp_str += '{'

			elif(char == '}'):
				if(composite_depth > 0):
					composite_depth -= 1
					temp_str += '}'
				else:
					ERROR("Unexpected closing brace", line_number, file)

			elif(char == '"' and in_string == False):
				if(temp_str == ""):
					in_string = True
					temp_str += '"'
				else:
					ERROR("Unexpected text before opening quotation mark", line_number, file)

			elif(char == '"' and in_string == True):
				in_string = False
				was_string = True
				temp_str += '"'

			elif(char == ' ' and in_string == False and composite_depth <= 0):
				token = parser.parse_token(temp_str, token_arr, last_instruction_index, line_number, file)
				if(token in [parser.instruction, parser.label]):
					last_instruction_index = len(token_arr)
				token.set_line_number(line_number)
				token.set_file(file)
				token_arr.append(token)
				was_string = False
				temp_str = ""

			elif(char in '\n;'):
				if(in_string == True and char == '\n'):
					ERROR("String not closed", line_number, file)
				elif(composite_depth > 0 and char == '\n'):
					ERROR("Braces not closed", line_number, file)
				elif(token_arr[-1] == parser.line_break and temp_str == "" and token_arr[-1].preserve_line_number == False):
					line_number += 1
				elif(temp_str == ""):
					pass
				else:
					token = parser.parse_token(temp_str, token_arr, last_instruction_index, line_number, file)
					if(token in [parser.instruction, parser.label]):
						last_instruction_index = len(token_arr)
					token.set_line_number(line_number)
					token.set_file(file)
					token_arr.append(token)
					was_string = False
					temp_str = ""
					last_instruction_index = len(token_arr)
					if(char == "\n"):
						line_number += 1
						token_arr.append(parser.line_break(False))
						token_arr[-1].set_line_number(line_number-1)
						token_arr[-1].set_file(file)
					else:
						token_arr.append(parser.line_break(True))
						token_arr[-1].set_line_number(line_number)
						token_arr[-1].set_file(file)
			else:
				temp_str += char
			prev_char = char

		return(token_arr[1:])

	def from_file(file_path: str):
		try:
			return(parser.from_string(open(file_path).read(), file_path))
		except OSError:
			GLOBAL_ERROR(f"File '{file_path}' not found")

	def from_file_import(file_path: str, line_number: int, file: str):
		try:
			return(parser.from_string(open(file_path).read(), file_path))
		except OSError:
			ERROR(f"File '{file_path}' not found", line_number, file)

	def trim_text(text: str):
		out_str = ""
		lines = []
		for line in text.split('\n'):
			line += '\n'
			split = line.split(';')
			for i, line2 in enumerate(split):
				if(i < len(split)-1):
					line2 += ';'
				lines.append(line2)
		for index, line in enumerate(lines):
			line = line.strip('\t \n')
			line = line
			lines[index] = ""
			if(line != "" and line[0] not in '#'):
				for char in line:
					if(char == '#'):
						break
					else:
						lines[index] += char
		for line in lines:
			out_str += line.strip('\t ') + '\n'
		return(out_str)

	def to_string(token_arr: list):
		out_str = ""
		for token in token_arr:
			if(token == parser.line_break):
				out_str += str(token)
			else:
				out_str += str(token) + ' '
		return(out_str)