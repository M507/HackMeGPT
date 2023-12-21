import re

def sanitize_input(user_input):
    # Sanitize user input to prevent NoSQL injection
    # You may need to customize this based on your specific requirements
    return re.sub(r'[^a-zA-Z0-9_\-]', '', user_input)


# List of user inputs with potential NoSQL injection payloads
user_inputs = [
    "' || '1' == '1",  # SQL-like injection attempt
    '{"$ne": null}',   # MongoDB $ne operator for inequality
    '{"$gt": ""}',     # MongoDB $gt operator for greater than
    '{"$gt": {"$gt": ""}}',  # Nested MongoDB operators
    '{"$where": "this.field == \'some_value\' || true"}' , # MongoDB $where operator with JavaScript
    "what's that?",
    "<script>alert(1)</script>"
]

# Test the code with the list of user inputs
for user_input in user_inputs:
    result_message = sanitize_input(user_input)
    print(f"User input: {user_input}")
    print(f"sanitize_input: {result_message}")
    # print(result_message)
    print("--------------------")