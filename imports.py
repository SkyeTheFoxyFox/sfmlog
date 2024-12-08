from util import *
from parse import parser

class imports:
	def handle_imports(tokens):
		out_code = []
		import_list = [tokens[0].file]
		code = tokens.copy()
		while True:
			try:
				token = code.pop(0)
			except IndexError:
				break
			if(token == parser.instruction and token.value == "import"):
				temp_import = code.pop(0)
				path = ""
				if(temp_import.value[0] != "/"):
					path = temp_import.file.rsplit("/", 1)[0] + '/' + temp_import.value
				else:
					path = temp_import.value
				consume = None
				while(consume != parser.line_break):
					consume = code.pop(0)
				if(temp_import not in [parser.string_literal, parser.variable]):
					ERROR("Unexpected value following 'import'", temp_import.line_number, temp_import.file)
				if(path not in import_list):
					import_list.append(path)
					code = parser.from_file_import(path, temp_import.line_number, temp_import.file) + code
			else:
				out_code.append(token)
		return(out_code)


		


