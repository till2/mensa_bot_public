import http.client
import json
from termcolor import colored, cprint
 
def connect_to_server():
    # Setup the connection to your local server
    global conn
    conn = http.client.HTTPConnection("127.0.0.1", 1337)
    print("Connected to server.")

def disconnect_from_server():
    global conn
    if conn:
        conn.close()
        print("Disconnected from server.")

def get_response(prompt, system_prompt, temperature=0.7, top_p=0.95):
    # Define the headers and payload, using the "Mistral Instruct 7B Q4" model
    headers = {'Content-Type': "application/json"}    
    payload = json.dumps({
        "messages": [
            {
                "content": system_prompt,
                "role": "system"
            },
            {
                "content": prompt,
                "role": "user"
            }
        ],
        "model": "llama3-70b-8192",  # "mistral-ins-7b-q4" | groq llama3 70b: "llama3-70b-8192"
        "stream": False,
        "max_tokens": 1000,
        "stop": [],
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "temperature": 0.7, # 0.7
        "top_p": 0.95, # 0.95
    })


    # Make the POST request
    conn.request("POST", "/v1/chat/completions", payload, headers)

    # Get the response
    res = conn.getresponse()
    data = res.read()

    response = json.loads(data.decode("utf-8"))

    # Print the response
    # response
    # response.keys()
    # response["choices"][0].keys()
    # print(response)
    try:
        answer = response["choices"][0]["message"]["content"]
        return answer
    except KeyError:
        return "Too many requests."

if __name__ == "__main__":
    print(colored("[Type 'stop' to stop]", attrs=['bold']) + "\n")
    connect_to_server()

    temperature = 0.7
    top_p = 0.95
    system_prompt = "You are a helpful assistant."


    while True:
        prompt = input(colored("User: ", color="blue"))
        if prompt == "stop":
            break
        answer = get_response(prompt, system_prompt, temperature=temperature, top_p=top_p)
        print(colored("Model:", color="magenta"), answer + "\n")