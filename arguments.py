from util import *

class arguments:
	def __init__(self, argv):
		self.output_file = ""
		self.input_file = ""
		self.copy = False
		self.stdout = False

		self.args = argv[1:].copy()

		self.__handle_args__()

	def __pop_arg__(self):
		try:
			return(self.args.pop(0))
		except IndexError:
			return(None)

	def __handle_args__(self):
		while(self.args != []):
			arg = self.__pop_arg__()
			if(arg[0] != '-'):
				GLOBAL_ERROR(f"Expected '-' at the beginning of argument")
			arg = arg[1:]
			try:
				if('__' in arg):
					GLOBAL_ERROR(f"Unknown argument '{arg}'")
				else:
					getattr(arguments, arg)(self)
			except AttributeError:
				GLOBAL_ERROR(f"Unknown argument '{arg}'")

	def src(self):
		self.input_file = self.__pop_arg__()
		if(self.input_file == None):
			GLOBAL_ERROR(f"Argument 'src' expected another value")

	def out(self):
		self.output_file = self.__pop_arg__()
		if(self.output_file == None):
			GLOBAL_ERROR(f"Argument 'out' expected another value")

	def copy(self):
		self.copy = True

	def stdout(self):
		self.stdout = True