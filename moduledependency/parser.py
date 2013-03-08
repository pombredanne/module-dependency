class ParseError(ValueError):

	def __init__(self, *args):
		super().__init__(*args)


class ParsedImport:

	def __init__(self, moduleName, relative):
		self.moduleName = moduleName
		self.relative = relative

	def isRelative(self):
		return self.relative

	def __repr__(self):
		return str(self)

	def __str__(self):
		if self.isRelative():
			importTypeStr = "relative"
		else:
			importTypeStr = "absolute"
		return "({}, {})".format(self.moduleName, importTypeStr)

	def __eq__(self, other):
		return (self.moduleName == other.moduleName and self.relative == other.relative)

	def __ne__(self, other):
		return (self.moduleName != other.moduleName or self.relative != other.relative)


class ImportParser:

	def __init__(self):
		self.clear()

	def clear(self):
		self.foundImports = []
		self.tokens = []
		self.index = 0

	def currentToken(self):
		if self.index < len(self.tokens):
			return self.tokens[self.index]
		else:
			return None

	def nextToken(self):
		self.index += 1
		return self.currentToken()

	def addImport(self, moduleName, isRelative):
		#print("IMPORT FOUND: {}, {}".format(moduleName, isRelative))
		self.foundImports.append( ParsedImport(moduleName, isRelative) )

	def parse(self, tokens):
		# If no tokens were given, don't bother trying to parse
		if len(tokens) == 0:
			return []

		self.clear()
		self.tokens = tokens

		token = self.currentToken()
		while token:
			print(token)
			if token.type == "import":
				self.parseImport()
			elif token.type == "from":
				print("HELLO!")
				self.parseFrom()
			else: # only go to next token if another parsing method was not called
				token = self.nextToken()

		temp = self.foundImports
		self.clear()

		return temp

	def parseImport(self):
		"""Parse an absolute import."""
		#print("Parsing import statement...")
		# Skip "import" keyword
		self.nextToken()
		# Get the full name of the module being imported
		moduleName = self.parseDottedIdentifier()
		# Now construct the full module name and add the import
		# as one that was found by the parser
		self.addImport(moduleName, False)

		#print("...done parsing import statement.")

	def parseDottedIdentifier(self):
		"""Parse a series of identifiers separated with the "." operator.

		Returns this series of identifiers as a string. If no valid
		identifier could be found immediately, then None is returned.

		"""
		#print("Parsing dotted identifier...")

		token = self.currentToken()
		if not token:
			raise ParseError("Unexpected end of tokens")
		# Check straight away if the next token is the "all" wildcard.
		# if it is, just return "*" as the identifier
		elif token.type == "*":
			return "*"
		# Also check if the first token is an identifier. A valid
		# dootted identifier must START with an "identifier" token
		elif token.type != "identifier":
			raise ParseError("Dotted identifier must start with an identifier token")

		name = ""
		lookingForDot = False
		while True:
			if lookingForDot:
				if not token: # if end of tokens has been reached
					break
				elif token.type == "identifier":
					break # this is valid - just means it's the end of the current dotted identifier
				elif token.type == ".":
					name += "."
					lookingForDot = False
				else:
					break
			else:
				if not token:
					raise ParseError("Unexpected end of tokens - trailing dot operator")
				elif token.type == "identifier":
					name += token.value
					lookingForDot = True
				elif token.type == ".":
					raise ParseError("Invalid identifier - two consecutive dot operators present")
				else: # end parsing dotted identifier
					break

			token = self.nextToken()

		if name == "":
			return None
		else:
			return name

	def parseFrom(self):
		"""Parse "from" import statements."""
		#print("Parsing from statement...")
		# Determine if the from statement is absolute or relative.
		# If it's relative, then the otken straight after the
		# "from" keyword should be a ".".
		token = self.nextToken()
		if not token:
			raise ParseError("Unexpected end of tokens")
		elif token.type == ".":
			isRelative = True
		else:
			# We manually go back one token as we skipped part of the root module name
			self.index -= 1
			isRelative = False

		# Find the ROOT module name
		rootModuleName = self.parseDottedIdentifier()
		if not rootModuleName:
			raise ParseError("Module identifier should follow a 'from' keyword")
		# The next token should now be an "import" token
		token = self.currentToken()
		if not token:
			raise ParseError("Unexpected end of tokens")
		elif token.type != "import":
			raise ParseError("'import' keyword should follow root moudle name in 'from' import statement: " + str(token))		
		# Now get the name of all the objects
		importedObjects = self.parseImportedObjects()

		# If there were no objects imported using the 'from' satement
		# then the statement is a syntax error so the parse will fail
		if len(importedObjects) == 0:
			raise ParseError("Poorly formed 'from' statement never imported any objects: " + str(token))
		# If the wildcard "all" was found in the list of imported objects,
		# the it overrides the other imported obects and the entire root
		# module was imported
		if "*" in importedObjects:
			self.addImport(rootModuleName, isRelative)
		# Add a found module for each of the imported objects
		else:	
			for obj in importedObjects:
				fullModuleName = "{}.{}".format(rootModuleName, obj)
				self.addImport(fullModuleName, isRelative)

		#print("...done parsing from statement")

	def parseImportedObjects(self):
		"""Parse series of dotted identifiers separated by commas.

		Return list of strings containing those dotted identifiers.

		"""
		#print("Parsing imported objects...")
		importedObjects = []
		importedObjects.append( self.parseDottedIdentifier() )
		token = self.currentToken()
		while self.currentToken() and self.currentToken().type == ",":
			self.nextToken() # skip comma operator
			importedObjects.append( self.parseDottedIdentifier() )

		#print("...done parsing imported objects.")

		return importedObjects
