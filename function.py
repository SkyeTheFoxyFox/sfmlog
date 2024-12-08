from util import *
from parse import parser

class functions:
	def find_functions(tokens, function_list):
		out_code = []
		token_iter = iter(tokens)

		for token in token_iter:
			if(token == parser.instruction and token.value == "deffun"):
				function_name = next(token_iter)
				function_args = consume_tokens_of_line(token_iter)
				function_code = []
				while True:
					function_token = None
					try:
						function_token = next(token_iter)
					except 
					if(function_token == parser.instruction and function_token.value == "endfun"):
						consume_tokens_of_line(token_iter)
						break
					elif(function_token == parser.instruction and function_token.value == "deffun"):
						ERROR("Can't define a function within a function", macro_token.line_number, macro_token.file)
					else:
						function_code.append(function_token)

			else:


	def expand_functions(tokens, function_list):
		pass

	def expand_function_calls(tokens, function_list, used_function_list):
		pass

	def append_functions(tokens, function_list, used_function_list):
		pass

def consume_tokens_of_line(iterable_tokens):
	consumed_tokens = [next(iterable_tokens)]
	while consumed_tokens[-1] != parser.line_break:
		consumed_tokens.append(next(iterable_tokens))
	consumed_tokens = consumed_tokens[:-1]
	return consumed_tokens