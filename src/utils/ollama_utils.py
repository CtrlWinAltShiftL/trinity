from ollama import Client
import yaml

class Chatter():

	def __init__(self):
		'''
		Creates an ollama chat interface.
		'''

		with open(r"src\config\config.yaml", "r") as f:
			config = yaml.safe_load(f)

		self.temperature = config['TEMPERATURE']
		self.model_name = config['MODEL_NAME']
		self.host = config['OLLAMA_LOCALHOST']

		self.client = Client(
		host=self.host
		)

	def chat(self, query: str) -> str:
		response = self.client.chat(model=self.model_name, messages=[
		{
			'role': 'user',
			'content': query,
		},
		
		])
		return response.message.content
	
	def generate(self, query: str, temp: float = None) -> str:
		if not temp:
			temp = self.temperature
		response = self.client.generate(
			model=self.model_name,
			prompt=query,
			stream=False,
			options={
				'temperature': temp
			}
			)


		return response.response

if __name__=='__main__':
	pass


		