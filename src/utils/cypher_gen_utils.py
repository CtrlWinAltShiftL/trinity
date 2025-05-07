from utils.neo4j_utils import Neo
from utils.ollama_utils import Chatter
import json, re

class CypherGenerator():
	
	def __init__(self):
		self.neo = Neo()
		self.chatter = Chatter()
		self.cypher = None
		self.schema = self.neo.schema()

	def get_prompt(self):
		'''
		Sets the user_prompt attribute if not provided.
		'''
		self.user_prompt = input("\nPlease enter a prompt: ")

	def get_nodes(self, suffix: str = ""):
		'''
		Identifies relevant nodes based on the schema.
		'''

		llm_query = f'''
		Forget everything.\n

		Based on the following user prompt and knowledge graph schema, 
		please identify the nodes and their properties which are relevant to the user prompt.\n\n

		User prompt: {self.user_prompt}\n\n
		Schema:\n {self.schema}\n\n

		Respond in JSON in the following format, and nothing else:\n

		{{
		"nodes":
			[{{
				"label": <YOUR NODE LABEL>
				"properties": [<LIST OF NODE PROPERTY CLASSES>]
			}}]
		}}\n\n

		Node labels should be abstract categories (e.g. 'Unit'), not instances (e.g. 'Unit #33')
		Property classes should be abstract categories (e.g. 'name'), not instances (e.g. 'John')
		
		{suffix}\n

		ONLY USE THE CONTEXT PROVIDED AND NOTHING ELSE.
		'''

		res = self.chatter.generate(
			llm_query
		)

		try:
			self.nodes = json.dumps(res)
		except json.JSONDecodeError as e:
			error = f'''
			Last time, the returned format was not JSON and the following error was returned: {e}.\n
			Please avoid this.\n
			Only return JSON.
			'''
			self.get_nodes(suffix = error)
		except Exception as e:
			raise ValueError(f'\n[ERROR]: Node generation failed with following error: {e}')

	def get_rels(self, suffix: str = ""):
		'''
		Identifies relevant relationships based on the schema
		'''

		llm_query = f'''
		Forget everything.\n

		Based on the following user prompt and knowledge graph schema, 
		please identify the relationships and their properties which are relevant to the user prompt.\n\n

		User prompt: {self.user_prompt}\n\n
		Schema:\n {self.schema}\n\n

		Respond with the Cypher relationships in the following example format:\n

		(node1)-[:RELATIONSHIP]->(node2)

		Property classes should be abstract categories (e.g. 'name') as opposed to instances (e.g. 'John')

		{suffix}\n

		ONLY USE THE CONTEXT PROVIDED AND NOTHING ELSE.
		'''

		res = self.chatter.generate(
			llm_query
		)

		try:
			self.rels = json.dumps(res)
		except json.JSONDecodeError as e:
			error = f'''
			Last time, the returned format was not JSON and the following error was returned: {e}.\n
			Please avoid this.\n
			Only return JSON.
			'''
			self.get_rels(suffix = error)
		except Exception as e:
			raise ValueError(f'\n[ERROR]: Relationship generation failed with following error: {e}')

	def get_props_from_prompt(self):
		'''
		Identifies relevant properties in the user prompt.
		'''

		llm_query = f'''
		You have previously identified the following nodes as relevant to the user prompt.\n\n

		Nodes:\n {self.nodes}\n\n

		Relationships:\n {self.rels}\n\n

		User prompt: {self.user_prompt}\n\n

		Output a JSON in the following format which shows the values of properties
		IF THE USER PROMPT MAKES IT CLEAR IF THEY EXIST:\n\n

		{{
		"relationships": [
		{{
			"label": <RELATIONSHIP LABEL>,
			"property": <PROPERTY OF VALUE IDENTIFIED IN USER PROMPT>
			"value": <VALUE FROM USER PROMPT>
		}},
		"nodes": [
		{{
			"label": <NODE LABEL>,
			"property": <PROPERTY OF VALUE IDENTIFIED IN USER PROMPT>
			"value": <VALUE FROM USER PROMPT>
		}}
		]
		}}\n\n

		If the user prompt is unclear, or is asking if it exists rather than
		stating that it does exist, do not include the value in the JSON.\n

		Only return this JSON.\n

		ONLY USE THE CONTEXT PROVIDED AND NOTHING ELSE.
		'''

		res = self.chatter.generate(
			llm_query
		)

		try:
			self.props = json.dumps(res)
		except json.JSONDecodeError as e:
			error = f'''
			Last time, the returned format was not JSON and the following error was returned: {e}.\n
			Please avoid this.\n
			Only return JSON.
			'''
			self.get_props_from_prompt(suffix = error)
		except Exception as e:
			raise ValueError(f'\n[ERROR]: Property value generation failed with following error: {e}')

	def test(self) -> str:
		'''
		Validates the Cypher self.cypher by attempting execution.

		Args:
			None
		
		Returns:
			valid:			bool				Returns True if the Cypher is valid
			res:			Neo4j.EagerResult	The Neo4j response, if valid. Else, the error.
		'''

		try:
			res = self.neo.query_graph(self.cypher)
		except Exception as e:
			return False, e
		return True, res
	
	def clean(self) -> str:
		'''
		Cleans the Cypher syntactically.
		'''

		rules = [
			'If there is any text other than Cypher, remove it',
			'Make sure the variable that is returned is referenced in the MATCH clause',
			'Only use "MATCH", "WHERE", "RETURN" and "LIMIT" functions.',
			'Ensure that all nodes are surrounding in brackets, e.g. (n:Node)',
			'Ensure that all relationships are surrounded in square brackets, e.g. [r:RELATIONSHIP]',
			'Node and property labels (names) should always follow directly after a colon, e.g. (n:MyNodeLabel)',
			'Node labels should follow CamelCase',
			'Relationship labels should follow SCREAMING_SNAKE_CASE',
			'Nodes and relationships should always have dashes between them, with arrow heads showing directionality (node)-[:RELATIONSHIP]->(node)',
			'If the Cypher has any "=" within curly brackets, replace them with ":"',
		]

		for rule in rules:

			cleaner_prompt = f'''
			Forget everything.\n
			Ensure the following Cypher query conforms to the following rule.\n\n
			Cypher:\n{self.cypher}\n\n
			Rule: {rule}\n\n
			ONLY return the updated Cypher, nothing else.
			'''

			self.cypher = self.chatter.generate(
			cleaner_prompt
		)
	
	def fix(self, errors: str) -> str:
		'''
		Fix the Cypher based on errors returned from the database.

		Args:
			errors:			str		The errors returned from the database.

		Returns:
			fixed_cypher_query:	str		The fixed Cypher cypher_query.
		'''

		fixer_prompt = f'''
		Forget everything.\n
		The following Cypher query is incorrect.
		It is your task to fix it based on the following errors:\n\n

		Cypher:\n
		{self.cypher}\n\n

		Errors:\n
		{errors}\n\n

		ONLY return Cypher, nothing else. DO NOT EXPLAIN.
		'''

		fixed_cypher_query = self.chatter.generate(
			fixer_prompt
		)

		return fixed_cypher_query

	def validate_against_schema(self) -> str:
		'''
		Attempts to validate the Cypher against the schema.

		Args:
			None

		Returns:
			valid_cypher_query:	str		The valid Cypher cypher_query.
		'''

		validater_prompt = f'''
		Forget everything.\n
		The following Cypher query must conform to the following schema.\n
		Return Cypher which conforms to the schema.\n\n
		Cypher:\n{self.cypher}\n\n
		Schema:\n{self.schema}
		'''

		validated_cypher_query = self.chatter.generate(
			validater_prompt
		)

		return validated_cypher_query

	def replace_equals_in_brackets(self):
		# Use regular expression to find '=' between '{' and '}'
		self.cypher = re.sub(r'(?<={)(.*?)(?=})', lambda match: match.group(0).replace('=', ':'), self.cypher)

	def check_cypher(self, suffix:str  = ""):
		llm_query = f'''
		Will the following Cypher answer the following question? If not, why?\n\n

		Question:\n{self.user_prompt}\n\n

		Cypher:\n{self.cypher}\n\n

		Answer in the following JSON format only:\n
		{{
		'answers_question': <True/False>,
		'reason': <REASONING>
		}}\n\n
		The value of 'answers_question must be True or False.
		Only respond with the JSON, nothing else.\n
		{suffix}
		'''

		res = self.chatter.generate(llm_query)

		try:
			check = json.loads(res)
		except Exception:
			self.check_cypher(
				suffix='''Double-check it the output only contains 
				the JSON format above, and nothing else.'''
				)
		
		if check['answers_question'] == True:
			pass
		elif check['answers_question'] == False:
			reason = check['reason']
			sfx = f'''
			Last time you incorrectly produced {self.cypher}.\n
			This did not answer the user prompt because {reason}.
			'''
			self.to_cypher(
				prompt = self.user_prompt,
				suffix = sfx
				)
		else:
			self.check_cypher(
				suffix='''Double-check that the JSON is correctly 
				formatted and that the value of 'answers_question' 
				is either True or False.'''
			)

	
	def to_cypher(
			self,
			prompt:str = None,
		 	fresh_attempt_limit: int = 5,
		 	refactor_attempt_limit: int = 5,
			suffix: str = ""
		 ):
		
		if not prompt:
			self.get_prompt()
		else:
			self.user_prompt = prompt

		self.get_nodes()
		self.get_rels()
		self.get_props_from_prompt()

		# Prelim test
		attempts = 0
		working = False

		# If prelim test failed
		while not working and attempts <= fresh_attempt_limit:

			llm_query = f"""
				You are writing Cypher queries based on the schema:\n
				{self.schema}\n

				Write Cypher to respond to the prompt:\n
				{self.user_prompt}\n

				Respond with Cypher and nothing else.\n
				{suffix}
				"""
			
			response = self.chatter.generate(
				llm_query
			)
			self.cypher = response
			self.replace_equals_in_brackets()

			working, output = self.test()

			if working:
				break

			refactor_attempts = 0

			while refactor_attempts <= refactor_attempt_limit:
				self.clean()
				self.replace_equals_in_brackets()
				working, output = self.test()
				if working:
					break

				self.cypher = self.fix(errors = output)
				self.replace_equals_in_brackets()
				working, output = self.test()
				if working:
					break

				refactor_attempts += 1
			
			if working:
				break

			attempts += 1
		
		self.check_cypher()

		if working:
			return self.cypher
		else:
			return None
