import re
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, ContextTypes, filters
from local_llm import connect_to_server, disconnect_from_server, get_response
from function_calling import ls, findfile, findregex
import time
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

default_temperature = 0.7
default_top_p = 0.95
default_system_prompt = "You are a helpful assistant."

temperature = 0.7
top_p = 0.95
# system_prompt = "You are a helpful assistant."
system_prompt = """You are a helpful assistant. To help, you can use functions when appropriate. To call a function, use its name followed by the necessary arguments within parentheses. You can also think before outputting any functions. Just make sure that you only call one function in your answer! Also make sure to output your function call in this format:
<function(arg1, arg2)>
Here, you should put as many arguments seperated by comma as the desired function takes. 

The available Functions are:
    ls(path)
        Description: Executes the Linux command "ls PATH" and returns the first 200 characters of the result.
        Input: path - the directory path for which you want to list contents.
        Output: First 200 characters of the list of files and directories in the specified path.
        
Example: <ls("/home/till/Desktop/ThinkCell/ai-in-practice-think-cell/sharepoint")>
Example Output:
     annotations   classification   images	 inference   models  'think-cell benchmark'

findfile(PATH, FILENAME)
    Description: Finds a file in a specified directory.
    Input:
        PATH - the directory path where you want to search.
        FILENAME - the name of the file you're looking for.
    Output: Full path(s) to the file matching the given name in the specified directory.
    Example 1: <findfile("/home/till/Desktop", "Untitled1.ipynb")>
    Example Output 1: /home/till/Desktop/university_mats/Datenanalyse - Machine Learning 1/Ben Zusammenfassungen/Untitled1.ipynb
/home/till/Desktop/AdvMLSeminar/Untitled1.ipynb
Example 2 (no result): <findfile("/home/till/Desktop", "Untitled2.ipynb")>
Example Output 2:

findregex(PATH, REGEX)
    Description: Finds files matching a regular expression in a specified directory.
    Input:
        PATH - the directory path where you want to search.
        REGEX - the regular expression pattern to match filenames against.
    Output: Full path(s) to the files matching the given regular expression in the specified directory.
    Example: <findregex("/home/till/Desktop", "*diffusion*.pdf")>
    Example Output: /home/till/Desktop/AdvMLSeminar/diffusion_tutorial.pdf
/home/till/Desktop/AdvMLSeminar/diffusion_representation_learning_mastersthesis.pdf
/home/till/Desktop/AdvMLSeminar/diffusion based representation learning.pdf

Modes:
a) If you receive a prompt without any function calling result (clearly marked as "Function call" and "Function call result"), you can either output a function call or give a direct answer if you think a function call is not useful to answer the query. Just remember to only output one function in your answer!

Example interaction for a:
Prompt:
Hi, which files do I have on my Desktop?

Answer:
<ls("/home/till/Desktop")>

b) If you receive a prompt with a function calling result at the end (and the function that produced this result), which are clearly marked as "Function Call" and "Function call result", you previously called a function and can now use the result to assist. If the result is not useful for the above prompt and you believe you can do better if you reformulate the function call compared to the previous call, you can use function calling again. Otherwise, you can also output to the user why the result was not helpful and try to answer as best as you can without any function call results. Only output one function call in your answer.

Example interaction (1/2) for b:
Prompt 1:
Hi, which files do I have on my Desktop?

Answer 1:
<ls("/home/user/Desktop")>

Prompt 2:
Hi, which files do I have on my Desktop?
Function call: <ls("/home/user/Desktop")>
Function call result:
ls: cannot access '/home/user/Desktop': No such file or directory

Answer 2:
[Thinking]
The directory with user does not exist, so I should find out how the user is called. For this, I can use the ls command:
<ls("/home")>

Prompt 3:
Hi, which files do I have on my Desktop?
Function call: <ls("/home/user/Desktop")>
Function call result:
ls: cannot access '/home/user/Desktop': No such file or directory
Function call:
<ls("/home")>
Function call result:
till

Answer 3:
<ls("/home/user/Desktop")>

Prompt 4:
Hi, which files do I have on my Desktop?
Function call: <ls("/home/user/Desktop")>
Function call result:
ls: cannot access '/home/user/Desktop': No such file or directory
Function call:
<ls("/home")>
Function call result:
till
Function call:
<ls("/home/user/Desktop")>
Function call result:
Ablage			    ETH_Hackathon-20240423T154112Z-001.zip  'papers and theses'
 AdvMLSeminar		    ETH_Hackathon_Kaggle		     Playground
 AI_Ethics		    GitHub				     Portfolio
 Anki2pdf		    hello.txt				     Praktikum
 APML			    HPI_Bachelor_Master_Uebergang	     __pycache__
 Autograding		   'hpi mats'				    'Reinforcement Learning'
 BDS   AF
 (Info: Result was trimmed off after 200 characters.)

Answer 4:
Here's a list of all the files and folders on your Desktop:
1. Ablage
2. AdvMLSeminar
3. AI_Ethics
4. Anki2pdf
5. APML
6. Autograding
7. BDS
8. ETH_Hackathon-20240423T154112Z-001.zip
9. papers and theses
10. ETH_Hackathon_Kaggle
11. Playground
12. GitHub
13. Portfolio
14. hello.txt
15. Praktikum
16. HPI_Bachelor_Master_Uebergang
17. __pycache__
18. hpi mats
19. Reinforcement Learning

Note that the result was trimmed off after 200 characters, so there might be more files in your Documents directory.


Please make sure to only call functions when it would really be helpful. For example for these prompts you should respond without any function calls:
Example 1: Hi!
Example 2: How's the wheather today?
Example 3: Write a script in python to generate fibonacci numbers

Also note that you have a maximum number of function calls, so use them wisely. Your remaining number will be displayed to you.
If your keyword search does not return anything useful, you can also use other search strategies, for example by listing the content of a folder to find out it's subdirectories, then listing these etc.
For certain queries it can also be helpful to list the content of a parent folder.
One last note, always make sure that your function calls match the format and that you put the arguments into the descripted format with "arg".
"""

GREEN_COLOR = "\033[0;32m"
ORANGE_COLOR = "\033[0;33m"
BLUE_COLOR = "\033[0;36m"
RESET_COLOR = "\033[0m"


async def hi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello, I'm the Mistral Bot! 👾")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global temperature, top_p, system_prompt
    await update.message.reply_text(f"Commands:\n/hi - Say hi\n/help - This message\n/restart - Restart the conversation and reset all parameters\n/temperature - Set the temperature (default: 0.7)\n/top_p - Set the top_p parameter (default: 0.95)\n/system_prompt - Set the system prompt\n\nCurrent parameters:\ntemperature:{temperature}\ntop_p={top_p}\nSystem prompt:\n{system_prompt[:200]}\n\n-by Till")

async def set_temperature_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Checks if a new temperature value is provided
    if context.args:
        try:
            new_temp = float(context.args[0])
            global temperature
            temperature = new_temp  # Update the global temperature variable
            await update.message.reply_text(f"Temperature set to {temperature}.")
        except ValueError:
            await update.message.reply_text("Please enter a valid number for temperature.")
    else:
        await update.message.reply_text("Please provide a temperature value.")

async def set_top_p_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Checks if a new top_p value is provided
    if context.args:
        try:
            new_top_p = float(context.args[0])
            global top_p
            top_p = new_top_p  # Update the global top_p variable
            await update.message.reply_text(f"Top_p set to {top_p}.")
        except ValueError:
            await update.message.reply_text("Please enter a valid number for top_p.")
    else:
        await update.message.reply_text("Please provide a top_p value.")

async def set_system_prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        new_prompt = ' '.join(context.args)
        global system_prompt
        system_prompt = new_prompt  # Update the global system prompt
        await update.message.reply_text(f"System prompt set to: {system_prompt[:200]}")
    else:
        await update.message.reply_text("Please provide a system prompt.")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # Restart parameters
    global temperature, top_p, system_prompt
    temperature = default_temperature
    top_p = default_top_p
    system_prompt = default_system_prompt
    await update.message.reply_text("Reset all parameters.")

    try:
        disconnect_from_server()  # Close the existing connection
        connect_to_server()       # Re-establish a new connection
        await update.message.reply_text("Server connection restarted successfully.")
    except Exception as e:
        await update.message.reply_text(f"Failed to restart server connection: {e}")

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global system_prompt, temperature, top_p
#     message_type = update.message.chat.type # group | private
#     user_id = update.message.chat.id
#     text = update.message.text # incoming message

#     print(f"User: user_id: {user_id}, message_type: {message_type}, text: {text}")

#     # get response from LLM
#     answer = get_response(text, system_prompt, temperature=temperature, top_p=top_p)
#     print("Bot:", answer + "\n")

#     # send reply
#     await update.message.reply_text(answer)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global system_prompt, temperature, top_p
    message_type = update.message.chat.type  # group | private
    user_id = update.message.chat.id
    text = update.message.text  # incoming message

    print(f"User: user_id: {user_id}, message_type: {message_type}, text: {text}")

    result = handle_function_call(text)
    await update.message.reply_text(result)

def handle_function_call(text):

    # for loop to handle multiple function calls and model responses (be careful with this, because the prompt gets extended each time.)
    max_function_calls = 10
    for i in range(max_function_calls+1):

        # Regular expression pattern to match function calls
        function_call_pattern = r'<(ls|findfile|findregex)\(\"(.*?)\"(?:,\s*\"(.*?)\")?\)>'

        # avoid too many requests to JanAI
        time.sleep(3 if i == 0 else 5)

        print(f"{ORANGE_COLOR}[Text before function call]\n'''\n{text}\n'''\n{RESET_COLOR}")
        answer_pre_function_call = get_response(text, system_prompt, temperature=temperature, top_p=top_p)
        print(f"{BLUE_COLOR}[Bot]\n{answer_pre_function_call}{RESET_COLOR}\n")

        # Search for function calls in the incoming message
        function_calls = re.findall(function_call_pattern, answer_pre_function_call)

        def clean_matches(matches):
            cleaned = []
            for match in matches:
                # Filter out empty strings and form a new tuple, then append to cleaned list
                cleaned.append(tuple(filter(lambda x: x != '', match)))
            return cleaned

        function_calls = clean_matches(function_calls)

        # If there were no function calls, generate response from LLM
        if not function_calls:
            return answer_pre_function_call

        # Execute only one function call and send the result as a reply
        print(f"{GREEN_COLOR}[INFO] Doing a function call ({i+1}/{max_function_calls}).{RESET_COLOR}")
        function, *arguments = function_calls[0]

        #print(function)
        #print(arguments)

        # avoid too many requests to JanAI
        time.sleep(3 if i == 0 else 5)

        if function == "ls":
            # Execute ls command
            print(f"{GREEN_COLOR}[INFO] Executing function call: {function}({arguments[0]}){RESET_COLOR}")

            result = ls(arguments[0])
            function_call_text = f"Function call: <{function}({arguments})>"
            function_call_result = f"Function call result: {result}"
            text = f"{text}\n{function_call_text}\n{function_call_result}"

        elif function == "findfile":
            # Parse arguments for findfile function
            print(f"{GREEN_COLOR}[INFO] Executing function call: {function}({arguments[0]}, {arguments[1]}){RESET_COLOR}")

            path, filename = arguments
            result = findfile(path.strip(), filename.strip())
            function_call_text = f"Function call: <{function}({path.strip()}, {filename.strip()})>"
            function_call_result = f"Function call result: {result}"
            text = f"{text}\n{function_call_text}\n{function_call_result}"
            
        elif function == "findregex":
            # Parse arguments for findregex function
            print(f"{GREEN_COLOR}[INFO] Executing function call: {function}({arguments[0]}, {arguments[1]}){RESET_COLOR}")

            path, regex = arguments
            result = findregex(path.strip(), regex.strip())
            function_call_text = f"Function call: <{function}({path.strip()}, {regex.strip()})>"
            function_call_result = f"Function call result: {result}"
            text = f"{text}\n{function_call_text}\n{function_call_result}"

        text += f"\n(You have a maximum of {max_function_calls-i-1} function calls remaining (please output an answer if you have 0 function calls remaining, otherwise you can continue if you want).)"

            # Append function call results to the prompt and generate response from LLM
            # print(f"{ORANGE_COLOR}[INFO] Updated prompt after function call: {text}{RESET_COLOR}")

            # text = get_response(text, system_prompt, temperature=temperature, top_p=top_p) # answer
            #print("Bot:", answer + "\n")
            #return answer
    
    return f"Unfortunately your request exceeded my limit after 5 steps of function calling."


def main():
    print("Starting bot...")
    app = ApplicationBuilder().token(token).build()
    connect_to_server()

    # Commands
    app.add_handler(CommandHandler("hi", hi_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("restart", restart_command))
    app.add_handler(CommandHandler("temperature", set_temperature_command))
    app.add_handler(CommandHandler("top_p", set_top_p_command))
    app.add_handler(CommandHandler("system_prompt", set_system_prompt_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Poll the bot
    print("Polling...")
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()