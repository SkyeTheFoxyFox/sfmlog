import sys

def ERROR(message: str, line: int, file: str):
	print(f"ERROR at line {line} in file '{file}':", message)
	sys.exit(1)

def GLOBAL_ERROR(message: str):
	print(f"ERROR:", message)
	sys.exit(1)

from parse import parser

def print_token(token: parser.token):
	if(token == parser.line_break):
		return(f"{token.file}, {token.line_number}: {token.__class__.__name__}")
	elif(token == parser.composite_variable):
		s = ""
		for subtoken in token.tokens:
			s += f"({print_token(subtoken)}), "
		return(f"{token.file}, {token.line_number}: {token.__class__.__name__}: {token.format_value}: [{s[:-2]}]")
	else:
		return(f"{token.file}, {token.line_number}: {token.__class__.__name__}: {token}")

def read_line(code: list[parser.token]) -> list[parser.token]:
	consume = None
	output: list[parser.token] = []
	while(consume != parser.line_break):
		consume = code.pop(0)
		output.append(consume)
	return output[0:-1]

#def arg_index(line: list[parser.token], index: int, should_error = False, error_msg = "Argument {index} expected but not found") -> parser.token or None:
#	try:
