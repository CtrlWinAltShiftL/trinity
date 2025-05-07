cypher = '''
MATCH (n:PERSON {name = 'nick'})-[:KNOWS]->(p:PERSON)
RETURN n LIMIT 1
'''

import re

def replace_equals_in_curly_brackets(input_string):
    # Use regular expression to find '=' between '{' and '}'
    output_string = re.sub(r'(?<={)(.*?)(?=})', lambda match: match.group(0).replace('=', ':'), input_string)
    return output_string

# Test
input_string = "This is a {key=value} and another {anotherKey=anotherValue}"
output_string = replace_equals_in_curly_brackets(cypher)
print(output_string)
