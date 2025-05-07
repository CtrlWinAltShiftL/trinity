from utils.cypher_gen_utils import CypherGenerator
from utils.neo4j_utils import Neo
from utils.ollama_utils import Chatter

neo = Neo()
cygen = CypherGenerator()
chatter = Chatter()

prompt = "Does Nick know someone called Bob?"

cypher = cygen.to_cypher(prompt)

results = neo.query_graph(cypher)
	
response = chatter.generate(
	f'''
	Forget everything.\n
	Based on the following user prompt, use the evidence provided to respond to the prompt.\n\n
	Prompt: {prompt}\n\n
	Evidence: {results}
	'''
)

print(f'Answer: {response}\n\nEvidence: {results}')