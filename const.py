from parse import parser
from util import *

class consts:
	def find_consts(tokens, const_dict):
		out_code = []
		code = tokens.copy()
		while True:
			try:
				token = code.pop(0)
			except IndexError:
				break
			if(token == parser.instruction and token.value == "const"):
				key = code.pop(0)
				if(key != parser.variable):
					ERROR("Invalid key for 'const'", key.line_number, key.file)
				value = read_line(code)
				if(len(value) < 1):
					ERROR("Invalid value for 'const'", token.line_number, token.file)

				const_dict[key.value] = value

			elif(token == parser.instruction and token.value == "enum"):
				line = read_line(code)
				enum_value = 0
				while True:
					try:
						key = code.pop(0)
					except IndexError:
						ERROR("Unexpected end of file (maybe you forgot an 'endenum')", key.line_number, key.file)

					if key == parser.instruction and key.value == "endenum":
						read_line(code)
						break
					if(key != parser.instruction):
						ERROR("Invalid key for 'enum'", key.line_number, key.file)

					const_dict[key.value] = [parser.decimal_literal(str(enum_value))]
					enum_value += 1
					read_line(code)


			else:
				out_code.append(token)
		return(out_code)

	def expand_consts(tokens, const_dict):
		out_code = []
		for token in tokens:
			if(token in [parser.instruction, parser.sub_instruction, parser.variable] and token.value in const_dict):
				#print(token.value)
				for const_token in const_dict[token.value]:
					out_code.append(const_token)
					out_code[-1].set_file(token.file)
					out_code[-1].set_line_number(token.line_number)
			else:
				out_code.append(token)
		return(out_code)