from neo4j import GraphDatabase
import os
import json

class Neo():
	'''
	Neo4j connection module with useful functions.
	'''

	def __init__(self):
		'''
		Creates a Neo4j driver.
		'''
		self.auth = (
			os.environ.get('NEO4J_USERNAME'),
			os.environ.get('NEO4J_PASSWORD')
			)
		self.uri = os.environ.get('NEO4J_URI')
		self.driver = GraphDatabase.driver(uri=self.uri, auth=self.auth)
		self.driver.verify_connectivity()

	def query_graph(self, query: str) -> list:
		'''
		Executes a query against the connected graph and returns a list of results.

		Args:
			query:	str		The user input query to be executed
		
		Returns:
			res:	list	A list of results from the graph
			
		'''
		restricted_words = [
			'delete',
			'set',
			'merge',
			'create'
		]
		for word in restricted_words:
			if word in query.lower():
				raise PermissionError(f'ERROR: Query attempting to perform {word} operation. This is not permitted.')
			
		query = query.replace("\\n", " ")
		query = query.replace("`","")
		print(f'\n{query}')
		res = [a for a in self.driver.execute_query(query).records]
		return res
	
	def schema(self) -> str:
		'''
		Returns the schema of the graph as JSON-formatted string.
		'''
		#res = self.driver.execute_query('CALL apoc.meta.schema()').records[0]['value']
		#return json.dumps(res)

		nodes_query = f'''
		MATCH (n) RETURN DISTINCT labels(n) as node_label, keys(n) as node_properties
		'''

		res = self.driver.execute_query(nodes_query)

		nodes = {}

		for record in res.records:
			nodes[record['node_label'][0]] = {
				'properties': record['node_properties']
			}

		relationships_query = f'''
		MATCH ()-[r]->() RETURN DISTINCT TYPE(r) as rel_type, keys(r) as rel_properties
		'''

		res = self.driver.execute_query(relationships_query)

		rels = {}

		for record in res.records:
			rels[record['rel_type']] = {
				'properties': record['rel_properties']
			}

		schema_query = f'''
		MATCH (n)-[r]->(m) WHERE elementId(n)<>elementId(m)
		RETURN DISTINCT(LABELS(n)) as node1, TYPE(r) as rel, LABELS(m) as node2
		'''

		res = self.driver.execute_query(schema_query)

		schema_strings = []

		for record in res.records:
			node1 = record['node1'][0]
			rel = record['rel']
			node2 = record['node2'][0]

			schema_string = f'(:{node1})-[:{rel}]->(:{node2})'

			schema_strings.append(schema_string)

		schema = '\n'.join(schema_strings)

		return f'Nodes:\n{nodes}\n\nRelationships:\n{rels}\n\nSchema:\n{schema}'
	
if __name__ == '__main__':
	neo = Neo()
	res = neo.schema()
	print(res)
