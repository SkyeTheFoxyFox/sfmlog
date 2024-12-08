from util import *
from parse import parser

class pre_exec:
	
	INSTRUCTIONS = ['pset', 'pop', 'spop', 'if', 'endif', 'for', 'endfor', 'while', 'endwhile']

	OUTPUT_MAP = {
		'pset': [True],
		'pop': [False, True],
		'spop': [False, True],
		'if': [],
		'endif': [],
		'for': [True],
		'endfor': [],
		'while': [],
		'endwhile': []

	}

	def evaluate_code(tokens: list) -> list:
		out_code = []
		variables = {}
		instruction_pointer = 0
		while True:
			try:
				token = tokens[instruction_pointer]
			except IndexError:
				return tokens
			if(token == parser.instruction and token.value in pre_exec.INSTRUCTIONS):
				line = [token]

				instruction_pointer += 1
				t = tokens[instruction_pointer]
				while(t != parser.line_break):
					if(len(line)-1 not in range(len(pre_exec.OUTPUT_MAP[line[0].value])) or pre_exec.OUTPUT_MAP[line[0].value] == False):
						line.append(pre_exec.substitute_variable(t, variables))
					else:
						line.append(t)
					
					instruction_pointer += 1
					t = tokens[instruction_pointer]
				instruction_pointer = pre_exec.eval_instruction(out_code, tokens, instruction_pointer, line, variables)
			else:
				out_code.append(pre_exec.substitute_variable(token, variables))
				out_code[-1].set_line_number(token.line_number)
				out_code[-1].set_file(token.file)
			instruction_pointer += 1
			if(instruction_pointer >= len(tokens)-1):
				break
		return(out_code)

	def substitute_variable(token, variables):
		if(token in [parser.variable, parser.global_variable] and token.value in variables):
			return(variables[token.value])
		elif(token == parser.composite_variable):
			out_tokens = []
			for sub_token in token.tokens:
				out_tokens.append(pre_exec.substitute_variable(sub_token, variables))
			return(parser.parse_token(token.format_value.format(*out_tokens), [parser.token], 0, token.line_number, token.file))
		else:
			return(token)

	def eval_instruction(output_code, input_code, instruction_pointer, exec_line, variables):
		line = exec_line[0].line_number
		file = exec_line[0].file

		match(exec_line[0].value):
			case "pset":
				if(len(exec_line) < 3):
					ERROR("Unexpected end of line", line, file)
				if(exec_line[1] not in [parser.variable, parser.global_variable]):
					ERROR("Invalid variable name", line, file)
				variables[exec_line[1].value] = exec_line[2]

			case "pop":
				if(len(exec_line) < 4):
					ERROR("Unexpected end of line", line, file)
				if(exec_line[2] not in [parser.variable, parser.global_variable]):
					ERROR("Invalid variable name", line, file)

				if(len(exec_line) <= 4):
					if(not exec_line[3].NUMERIC):
						ERROR("Expected numeric input", line, file)
					output = pre_exec.eval_pop(exec_line[1].value, exec_line[3].float, 0, line, file)
					if(output == int(output)):
						output = int(output)
					variables[exec_line[2].value] = parser.decimal_literal(str(output))
					variables[exec_line[2].value].set_line_number(line)
					variables[exec_line[2].value].set_file(file)
				else:
					if(not exec_line[3].NUMERIC or not exec_line[4].NUMERIC):
						ERROR("Expected numeric input", line, file)
					output = pre_exec.eval_pop(exec_line[1].value, exec_line[3].float, exec_line[4].float, line, file)
					if(output == int(output)):
						output = int(output)
					variables[exec_line[2].value] = parser.decimal_literal(str(output))
					variables[exec_line[2].value].set_line_number(line)
					variables[exec_line[2].value].set_file(file)
			case "spop":
				if(len(exec_line) < 4):
					ERROR("Unexpected end of line", line, file)
				if(exec_line[2] not in [parser.variable, parser.global_variable]):
					ERROR("Invalid variable name", line, file)

				if(len(exec_line) <= 4):
					if(exec_line[3] != parser.string_literal):
						ERROR("Expected string input", line, file)
					output = pre_exec.eval_spop(exec_line[1].value, exec_line[3].value, 0, line, file)
					variables[exec_line[2].value] = parser.string_literal(str(output))
					variables[exec_line[2].value].set_line_number(line)
					variables[exec_line[2].value].set_file(file)
				else:
					if(exec_line[3] != parser.string_literal or exec_line[4] != parser.string_literal):
						ERROR("Expected string input", line, file)
					output = pre_exec.eval_spop(exec_line[1].value, exec_line[3].value, exec_line[4].value, line, file)
					variables[exec_line[2].value] = parser.string_literal(str(output))
					variables[exec_line[2].value].set_line_number(line)
					variables[exec_line[2].value].set_file(file)
			case "if":
				if(len(exec_line) < 4):
					ERROR("Unexpected end of line", line, file)
				if(not pre_exec.eval_condition(exec_line[1].value, exec_line[2], exec_line[3], line, file)):
					depth = 1
					while True:
						instruction_pointer += 1
						token = input_code[instruction_pointer]
						if(instruction_pointer >= len(input_code)-1):
							ERROR("If statement not closed", line, file)
						if(token == parser.instruction and token.value == "if"):
							depth += 1
						if(token == parser.instruction and token.value == "endif"):
							depth -= 1
						if(depth == 0):
							t = input_code[instruction_pointer]
							while(t != parser.line_break):
								instruction_pointer += 1
								t = input_code[instruction_pointer]
							break
			case "while":
				if(len(exec_line) < 4):
					ERROR("Unexpected end of line", line, file)
				if(not pre_exec.eval_condition(exec_line[1].value, exec_line[2], exec_line[3], line, file)):
					depth = 1
					while True:
						instruction_pointer += 1
						token = input_code[instruction_pointer]
						if(instruction_pointer >= len(input_code)-1):
							ERROR("While loop not closed", line, file)
						if(token == parser.instruction and token.value == "while"):
							depth += 1
						if(token == parser.instruction and token.value == "endwhile"):
							depth -= 1
						if(depth == 0):
							t = input_code[instruction_pointer]
							while(t != parser.line_break):
								instruction_pointer += 1
								t = input_code[instruction_pointer]
							break
			case "endwhile":
				depth = 0
				while True:
					instruction_pointer -= 1
					token = input_code[instruction_pointer]
					if(instruction_pointer < 0):
						ERROR("Unexpected 'endwhile'", line, file)
					if(token == parser.instruction and token.value == "endwhile"):
						depth += 1
					if(token == parser.instruction and token.value == "while"):
						depth -= 1
					if(depth == 0):
						instruction_pointer -= 1
						break

			#case _:
			#	print(exec_line)
		return instruction_pointer

	def eval_pop(operation, a, b, line, file):
		match operation:
			case "add":
				return(a + b)
			case "sub":
				return(a - b)
			case "mul":
				return(a * b)
			case "div":
				return(a / b)
			case "idiv":
				return(a // b)
			case "mod":
				return(a % b)
			case "pow":
				return(pow(a,b))
			case "equal":
				return(a == b)
			case "notEqual":
				return(a != b)
			case "land":
				return(a and b)
			case "lessThan":
				return(a < b)
			case "lessThanEq":
				return(a <= b)
			case "greaterThan":
				return(a > b)
			case "greaterThanEq":
				return(a >= b)
			case "strictEqual":
				return(a == b)
			case "shl":
				return(int(a) << int(b))
			case "shr":
				return(int(a) >> int(b))
			case "or":
				return(int(a) | int(b))
			case "and":
				return(int(a) & int(b))
			case "xor":
				return(int(a) ^ int(b))
			case "not":
				return(~int(a))
			case "max":
				return(max(a, b))
			case "min":
				return(min(a, b))
			case "angle":
				return(math.degrees(math.atan2(a, b)))
			case "angleDiff":
				a = ((a % 360) + 360) % 360
				b = ((b % 360) + 360) % 360
				return(min(a - b + 360 if (a - b) < 0 else a - b, b - a + 360 if (b - a) < 0 else b - a))
			case "len":
				return(math.hypot(a, b))
			case "noise":
				WARNING("No noise idiot")
				return(0)
			case "abs":
				return(abs(a))
			case "log":
				return(math.log(a))
			case "log10":
				return(math.log10(a))
			case "floor":
				return(math.floor(a))
			case "ceil":
				return(math.ceil(a))
			case "sqrt":
				return(math.sqrt(a))
			case "rand":
				return(random.uniform(0,a))
			case "sin":
				return(math.sin(a))
			case "cos":
				return(math.cos(a))
			case "tan":
				return(math.tan(a))
			case "asin":
				return(math.asin(a))
			case "acos":
				return(math.acos(a))
			case "atan":
				return(math.atan(a))
			case _:
				ERROR(f"Unknown operation \"{operation}\"", line, file)

	def eval_spop(operation, a, b, line, file):
		match operation:
			case "cat":
				return(a + b)
			case _:
				ERROR(f"Unknown operation '{operation}'", line, file)

	def eval_condition(operation, a, b, line, file):
		v1 = a.float if a.NUMERIC else a.value
		v2 = b.float if b.NUMERIC else b.value
		match operation:
			case "equal":
				return(v1 == v2)
			case "notEqual":
				return(v1 != v2)
			case "lessThan":
				return(v1 < v2)
			case "greaterThan":
				return(v1 > v2)
			case "lessThanEq":
				return(v1 <= v2)
			case "greaterThanEq":
				return(v1 >= v2)
			case _:
				ERROR(f"Unknown comparison \"{operation}\"", line, file)