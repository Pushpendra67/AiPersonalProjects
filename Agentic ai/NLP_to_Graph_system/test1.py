
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
import time
import base64
import csv
import shutil
import threading
import autogen
from autogen import ConversableAgent 
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.io.base import IOStream
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
from autogen import AssistantAgent, UserProxyAgent
from autogen.code_utils import content_str
from autogen.exception_utils import AgentNameConflict, NoEligibleSpeaker, UndefinedNextAgent
from autogen.formatting_utils import colored
from autogen.graph_utils import check_graph_validity, invert_disallowed_to_allowed
from autogen.io.base import IOStream
from autogen.oai.client import ModelClient
from autogen.runtime_logging import log_new_agent, logging_enabled
from autogen import Agent
from autogen import GroupChat
from flask_cors import CORS

logger = logging.getLogger(__name__)

from system_messages import nlptosqlagent_system_message,sqltopython_system_message, graph_system_message

app=Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8298"}})
socket_io = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
# --------------------------------------------------------------------------------------------------->>


# llm_config = {"config_list": [{
#         "model": "gemma-2-2b-it",
#         "base_url": "http://localhost:1234/v1",
#         "api_key": "noneaadi",
#     }]}



llm_config = { 

    "config_list": [ 
        
        { 
            "model": "gpt-4", 
            "api_key": "***", 
            "base_url": "**", 
            "api_version": "2023-03-15-preview", 
            "api_type": "azure" ,
            "cache_seed": None
        } 

    ] 
}

Userinputagent = ConversableAgent(
    name="Userinputagent",
    llm_config=False,  
    human_input_mode="ALWAYS",
    is_termination_msg=None,
)

nlptosqlagent = ConversableAgent(
    name="nlptosqlagent",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    max_consecutive_auto_reply=100,
    is_termination_msg=None,
    code_execution_config={"use_docker": False},
    system_message=nlptosqlagent_system_message  ,
)

summaryprovider = AssistantAgent(
    name="summaryprovider",
    llm_config=llm_config, 
    human_input_mode="NEVER",
    max_consecutive_auto_reply=100,
    is_termination_msg=None,
    system_message="""you are a NATURAL LANGUAGE ANSWER provider agent . You are strictly adhere to anlayse the conversation of only two agents { Userinputagent ,code_executor_agent }. Here , Userinputagent Ask a query and code executor agent provide the output of the query asked.
    you have to first understand all the userquery and then understand the ooutput of code executor to that query , Then provide answer to user in NATURAL LANGUAGE about the result and what user has asked.
    **YOU are strictly adhere not to take any conversation from other agents except two agents { Userinputagent ,code_executor_agent }.**
    Do not include data youself only process the data that is provided to you by code executor agent.
      """ ,

)

sqltopython = ConversableAgent(
    name="sqltopython",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    code_execution_config=False,
     max_consecutive_auto_reply=100,
    is_termination_msg=None,
    #code_execution_config={"use_docker": False},
    system_message=sqltopython_system_message ,

)

# Create a temporary directory to store the code files.
temp_dir = "C:\\Users\\Pushpendra Singh\\Desktop\\AutoGen\\Localdir"

executor = LocalCommandLineCodeExecutor(
    timeout=200, 
    work_dir=temp_dir,
    execution_policies={ "python": True}

)

code_executor_agent = ConversableAgent(
    "code_executor_agent",
    llm_config=False,  
    code_execution_config={"executor": executor}, 
    human_input_mode="NEVER", 
     
      max_consecutive_auto_reply=100,
    is_termination_msg=None, 
)

code_executor_agent_second = ConversableAgent(
    "code_executor_agent_second",
    llm_config=False, 
    code_execution_config={"executor": executor},  
    human_input_mode="NEVER",

     max_consecutive_auto_reply=100,
    is_termination_msg=None,

)


graph_python_code_generatorAgent=ConversableAgent(
    name="graph_python_code_generatorAgent",
    llm_config=llm_config,  
    human_input_mode="NEVER",
    code_execution_config=False,
    system_message=graph_system_message ,

     max_consecutive_auto_reply=100,
    is_termination_msg=None,

)

LASTagent = ConversableAgent(
    name="LASTagent",
    llm_config=False,  
    human_input_mode="ALWAYS",
    code_execution_config=False,
    

    max_consecutive_auto_reply=100,
    is_termination_msg=None
)

Welcomeagent = ConversableAgent(
    name="Welcomeagent",
    llm_config=False,  
    human_input_mode="NEVER",
    code_execution_config=False,

     max_consecutive_auto_reply=100,
     
   system_message = """Welcome to SQL to Graph. You are an agent responsible for generating welcome messages. Please respond with the message 'Welcome to SQL to Graph' whenever called. YOu are strictly adhere not to say anthing else or dont do anyhting else only print welcome message."""
,
       is_termination_msg=None

)


IMAGES_FOLDER = 'C:\\Users\\Pushpendra Singh\\Desktop\\AutoGen\\Localdir'

def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
 
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        print(f"All content in the folder {folder_path} has been deleted.")
    else:
        print(f"The folder {folder_path} does not exist.")

def custom_speaker_selection(last_speakerr, groupchat):
   
    last_message = groupchat.messages[-1] 
    last_speaker = last_message['name']  
    
    if last_speaker == 'code_executor_agent_second':
         time.sleep(1)
        
         if 'exitcode: 1' in last_message['content']: 
            return graph_python_code_generatorAgent
         
         elif 'exitcode: 0' in last_message['content']:
            return LASTagent
         else:
             return LASTagent
         
         
    elif last_speaker == 'graph_python_code_generatorAgent':
        time.sleep(0.5)
        if 'import' not in last_message['content']:

            for key, messages in last_speakerr.chat_messages.items():
                last_speakerr.chat_messages[key] = [message for message in messages if message['name'] != 'summaryprovider']    

            message_added = False
            for key, messages in last_speakerr.chat_messages.items():
                if not message_added:
                    new_message = {
                        'content': 'Make the graph scripts according to provided data, don\'t use any random data.',
                        'name': 'graph_python_code_generatorAgent',
                        'role': 'system', 
                    }

                    last_speakerr.chat_messages[key].append(new_message)
                    message_added = True
            
            print("Missing import statements in the generated code, retrying...")
            return graph_python_code_generatorAgent
        else:
            time.sleep(1.5)
            print("Import statements found, proceeding to code execution...")
            return code_executor_agent_second
    
    # elif last_speaker == 'code_executor_agent':
    #     # return graph_python_code_generatorAgent
    #     if 'exitcode: 1' in last_message['content']:
    #         # print("==================================== EXECUTOR 1 AGENT GROUPCHAT MESSAGES===\n",groupchat.messages)
    #         return sqltopython
    #     elif 'exitcode: 0' in last_message['content']:
    #         # print("==================================== EXECUTOR 1 AGENT GROUPCHAT MESSAGES===\n",groupchat.messages)
    #         if 'error occurred' in last_message['content']:
    #             if 'Invalid column name' in last_message['content']:
    #                 return  nlptosqlagent
    #             return sqltopython  # Execution succeeded
    #         return graph_python_code_generatorAgent

    elif last_speaker == 'code_executor_agent':
        if 'exitcode: 1' in last_message['content']:
            return sqltopython
        elif 'exitcode: 0' in last_message['content']:
            if 'error occurred' in last_message['content']:
                if 'Invalid column name' in last_message['content']:
                    return  nlptosqlagent
                return sqltopython
            time.sleep(1.5)  
            return summaryprovider

    elif last_speaker == 'summaryprovider':
        return graph_python_code_generatorAgent    
      
    elif last_speaker == 'sqltopython':
        time.sleep(1)
        return code_executor_agent
    
    elif last_speaker == 'nlptosqlagent':
        if 'NOT_SATISFIED' in last_message['content']:
            return Userinputagent
        else:
            return sqltopython
    elif last_speaker == 'Userinputagent':
        return nlptosqlagent
    elif last_speaker == 'LASTagent':
        time.sleep(1)
       # clear_folder(IMAGES_FOLDER)
        return Welcomeagent
    
    elif last_speaker == 'Welcomeagent':
        return Userinputagent
    
    else:
        return Welcomeagent

groupchat = autogen.GroupChat(
   
  agents = [Welcomeagent,Userinputagent,nlptosqlagent, sqltopython,code_executor_agent,summaryprovider,graph_python_code_generatorAgent,code_executor_agent_second,LASTagent],
   # speaker_selection_method="manual",
#    allowed_or_disallowed_speaker_transitions=not_allowed_transitions,
#     speaker_transitions_type="disallowed",
    max_retries_for_selecting_speaker=10,
    max_round=100,
    # is_termination_msg=None,
    #is_termination_msg=termination_message,
    speaker_selection_method=custom_speaker_selection,
    enable_clear_history=True,
    messages=[]
)


manager = autogen.GroupChatManager(
    groupchat=groupchat,
    code_execution_config={"use_docker": False},
    max_consecutive_auto_reply=100,
    is_termination_msg=None,
    llm_config=llm_config,)

firsthumaninput=""

is_processing = False

_human_input = []




def new_get_human_input(prompt: str) -> str:
        global firsthumaninput
        print("this is prompt---->",prompt)
        if('Replying as LASTagent' in prompt):
            socket_io.emit('clear_history',{ 'clearhistory':True})
        elif('Replying as Userinputagent' in prompt):
            socket_io.emit('request_input', {'prompt': prompt,})
        
        while True:
            if _human_input:
                firsthumaninput= _human_input[0] 
                return _human_input.pop(0) 
            socket_io.sleep(0.1) 

# def new_print_message(message,sender):
#     global firsthumaninput 
#     print(f"--->{sender.name}:==>{type(message),message}")
#     if(sender.name=="Userinputagent"):
#         socket_io.emit('message',{"sender":sender.name,"content":firsthumaninput})
#         firsthumaninput=""
#     else:    
#         socket_io.emit('message',{"sender":sender.name,"content":message})


def new_print_message(message,sender):
    global firsthumaninput 
    print(f"--->{sender.name}:==>{type(message),message}")
    if(sender.name=="Userinputagent"):
        socket_io.emit('message',{"sender":sender.name,"content":firsthumaninput})
        firsthumaninput=""
    elif(sender.name=="Welcomeagent"): 
        socket_io.emit('message',{"sender":sender.name,"content":message})

    elif(sender.name=="summaryprovider"): 
        socket_io.emit('message',{"sender":sender.name,"content":message})    
    
    elif(sender.name=="nlptosqlagent"):
        socket_io.emit('message',{"sender":sender.name,"content":message})


        # if 'SATISFIED' in message:
        #     socket_io.emit('message',{"sender":sender.name,"content":"SATISFIED , processing ...."})
        # else:   
        #     socket_io.emit('message',{"sender":sender.name,"content":message}) 

    # elif(sender.name=="LASTagent"):   
    #     socket_io.emit('message',{"sender":sender.name,"content":message})
    # elif(sender.name=="code_executor_agent_second"):   
    #     socket_io.emit('message',{"sender":sender.name,"content":message})
    # elif(sender.name=="code_executor_agent"):   
    #     socket_io.emit('message',{"sender":sender.name,"content":message})


def new_clear_agents_history( reply, groupchat) -> str:
        """Clears history of messages for all agents or selected one. Can preserve selected number of last messages.
        That function is called when user manually provide "clear history" phrase in his reply.
        When "clear history" is provided, the history of messages for all agents is cleared.
        When "clear history <agent_name>" is provided, the history of messages for selected agent is cleared.
        When "clear history <nr_of_messages_to_preserve>" is provided, the history of messages for all agents is cleared
        except last <nr_of_messages_to_preserve> messages.
        When "clear history <agent_name> <nr_of_messages_to_preserve>" is provided, the history of messages for selected
        agent is cleared except last <nr_of_messages_to_preserve> messages.
        Phrase "clear history" and optional arguments are cut out from the reply before it passed to the chat.

        Args:
            reply (dict): reply message dict to analyze.
            groupchat (GroupChat): GroupChat object.
        """
        iostream = IOStream.get_default()
        if isinstance(reply, str):
            reply_content = reply
        else:
            reply_content = reply["content"] 

        # reply_content = reply["content"]
        # Split the reply into words
        words = reply_content.split()
        # Find the position of "clear" to determine where to start processing
        clear_word_index = next(i for i in reversed(range(len(words))) if words[i].upper() == "CLEAR")
        # Extract potential agent name and steps
        words_to_check = words[clear_word_index + 2 : clear_word_index + 4]
        nr_messages_to_preserve = None
        nr_messages_to_preserve_provided = False
        agent_to_memory_clear = None

        for word in words_to_check:
            if word.isdigit():
                nr_messages_to_preserve = int(word)
                nr_messages_to_preserve_provided = True
            elif word[:-1].isdigit():  # for the case when number of messages is followed by dot or other sign
                nr_messages_to_preserve = int(word[:-1])
                nr_messages_to_preserve_provided = True
            else:
                for agent in groupchat.agents:
                    if agent.name == word:
                        agent_to_memory_clear = agent
                        break
                    elif agent.name == word[:-1]:  # for the case when agent name is followed by dot or other sign
                        agent_to_memory_clear = agent
                        break
        # preserve last tool call message if clear history called inside of tool response
        if "tool_responses" in reply and not nr_messages_to_preserve:
            nr_messages_to_preserve = 1
            logger.warning(
                "The last tool call message will be saved to prevent errors caused by tool response without tool call."
            )
        # clear history
        if agent_to_memory_clear:
            if nr_messages_to_preserve:
                iostream.print(
                             f"Clearing history for {agent_to_memory_clear.name} except last {nr_messages_to_preserve} messages."
                            )
                agent_messages = [msg for msg in groupchat.messages if msg['name'] == agent_to_memory_clear.name]

                remaining_messages = [msg for msg in groupchat.messages if msg['name'] != agent_to_memory_clear.name]
                remaining_messages.extend(agent_messages[-nr_messages_to_preserve:])
                groupchat.messages = remaining_messages            
                            
                    
        # Filter messages for the agent to clear (remove messages by agent's name)
            else:
                iostream.print(f"Clearing all history for {agent_to_memory_clear.name}.")
                groupchat.messages = [msg for msg in groupchat.messages if msg['name'] != agent_to_memory_clear.name]
            agent_to_memory_clear.clear_history(nr_messages_to_preserve=nr_messages_to_preserve)
       
        else:
            if nr_messages_to_preserve:
                # iostream.print(f"Clearing history for all agents except last {nr_messages_to_preserve} messages for 'Userinputagent' and 'nlptosqlagent'.")
    
                # userinputagent_messages = [msg for msg in groupchat.messages if msg['name'] == 'Userinputagent']
                # nlptosqlagent_messages = [msg for msg in groupchat.messages if msg['name'] == 'nlptosqlagent']
    

                # preserved_userinputagent_messages = userinputagent_messages[-nr_messages_to_preserve:]
                # preserved_nlptosqlagent_messages = nlptosqlagent_messages[-nr_messages_to_preserve:]

                # groupchat.messages.clear()
                # groupchat.messages.extend(preserved_userinputagent_messages)
                # groupchat.messages.extend(preserved_nlptosqlagent_messages)
            
                iostream.print(f"Clearing history for all agents except last {nr_messages_to_preserve} messages.")
                # clearing history for groupchat here
                temp = groupchat.messages[-nr_messages_to_preserve:]
                groupchat.messages.clear()
                groupchat.messages.extend(temp)
            else:
                iostream.print("================================================Clearing history for all agents.========================================>"*2)
                # clearing history for groupchat here
               # groupchat.messages.clear()
            # clearing history for agents
            for index,agent in enumerate(groupchat.agents):
                if agent.name=='Userinputagent' or agent.name=='nlptosqlagent':
                    print(f"clearing history for recipeint ")
                    agent.clear_history(recipient ="sqltopython" , nr_messages_to_preserve = 5)
                    agent.clear_history(recipient ="code_executor_agent" , nr_messages_to_preserve = 5)
                    agent.clear_history(recipient ="graph_python_code_generatorAgent" , nr_messages_to_preserve = 5)
                    agent.clear_history(recipient ="code_executor_agent_second" , nr_messages_to_preserve = 5)
                    agent.clear_history(recipient ="LASTagent" , nr_messages_to_preserve = 5)
                    agent.clear_history(recipient ="summaryprovider" , nr_messages_to_preserve = 5)
                    
                else:
                    agent.clear_history()

        # Reconstruct the reply without the "clear history" command and parameters
        skip_words_number = 2 + int(bool(agent_to_memory_clear)) + int(nr_messages_to_preserve_provided)
        reply_content = " ".join(words[:clear_word_index] + words[clear_word_index + skip_words_number :])

        return reply_content

def run_chat(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[GroupChat] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Run a group chat."""
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]
        speaker = sender
        groupchat = config
        send_introductions = getattr(groupchat, "send_introductions", False)
        silent = getattr(self, "_silent", False)

        if send_introductions:
            # Broadcast the intro
            intro = groupchat.introductions_msg()
            for agent in groupchat.agents:
                self.send(intro, agent, request_reply=False, silent=True)
            # NOTE: We do not also append to groupchat.messages,
            # since groupchat handles its own introductions

        if self.client_cache is not None:
            for a in groupchat.agents:
                a.previous_cache = a.client_cache
                a.client_cache = self.client_cache
        for i in range(groupchat.max_round):
            self._last_speaker = speaker
            groupchat.append(message, speaker)
            # broadcast the message to all agents except the speaker
            for agent in groupchat.agents:
                if agent != speaker:
                    self.send(message, agent, request_reply=False, silent=True)
            if self._is_termination_msg(message) or i == groupchat.max_round - 1:
                # The conversation is over or it's the last round
                break
            try:
                # select the next speaker
                speaker = groupchat.select_speaker(speaker, self)
                if not silent:
                    iostream = IOStream.get_default()
                    iostream.print(colored(f"\nNext speaker: {speaker.name}\n", "green"), flush=True)
                # let the speaker speak
                reply = speaker.generate_reply(sender=self)
            except KeyboardInterrupt:
                # let the admin agent speak if interrupted
                if groupchat.admin_name in groupchat.agent_names:
                    # admin agent is one of the participants
                    speaker = groupchat.agent_by_name(groupchat.admin_name)
                    reply = speaker.generate_reply(sender=self)
                else:
                    # admin agent is not found in the participants
                    raise
            except NoEligibleSpeaker:
                # No eligible speaker, terminate the conversation
                break

            if reply is None:
                # no reply is generated, exit the chat
                break

            # check for "clear history" phrase in reply and activate clear history function if found
            if (
                groupchat.enable_clear_history
                and reply["content"]
                and "CLEAR HISTORY" in reply["content"].upper()
            ):
                
                
                reply["content"] = self.clear_agents_history(reply, groupchat)

            # The speaker sends the message without requesting a reply
            speaker.send(reply, self, request_reply=False, silent=silent)
            message = self.last_message(speaker)
        if self.client_cache is not None:
            for a in groupchat.agents:
                a.client_cache = a.previous_cache
                a.previous_cache = None
        return True, None


def clear_history(self, recipient: Optional[Agent] = None, nr_messages_to_preserve: Optional[int] = None):
        """Clear the chat history of the agent.

        Args:
            recipient: the agent with whom the chat history to clear. If None, clear the chat history with all agents.
            nr_messages_to_preserve: the number of newest messages to preserve in the chat history.
        """
        iostream = IOStream.get_default()
        if recipient is None:
            if nr_messages_to_preserve:
                for key in self._oai_messages:
                    nr_messages_to_preserve_internal = nr_messages_to_preserve
                    # if breaking history between function call and function response, save function call message
                    # additionally, otherwise openai will return error
                    first_msg_to_save = self._oai_messages[key][-nr_messages_to_preserve_internal]
                    if "tool_responses" in first_msg_to_save:
                        nr_messages_to_preserve_internal += 1
                        iostream.print(
                            f"Preserving one more message for {self.name} to not divide history between tool call and "
                            f"tool response."
                        )
                    # Remove messages from history except last `nr_messages_to_preserve` messages.
                    self._oai_messages[key] = self._oai_messages[key][-nr_messages_to_preserve_internal:]
            else:
                self._oai_messages.clear()
        else:
            print("this is oai messages----=====>",self._oai_messages)
            self._oai_messages[recipient].clear()
            if nr_messages_to_preserve:
                iostream.print(
                    colored(
                        "WARNING: `nr_preserved_messages` is ignored when clearing chat history with a specific agent.",
                        "yellow",
                    ),
                    flush=True,
                )





manager._print_received_message=new_print_message
manager.clear_agents_history=new_clear_agents_history
manager.run_chat=run_chat
 
Userinputagent.get_human_input=new_get_human_input
LASTagent.get_human_input=new_get_human_input


@socket_io.on('human_input')
def handle_human_input(data):
    user_input = data.get('input', '')
    if user_input:
        _human_input.append(user_input) 
        socket_io.emit('input_received', {'message': 'Input received!'})


IMAGES_FOLDER = 'C:\\Users\\Pushpendra Singh\\Desktop\\AutoGen\\Localdir'

@app.route("/run")
def run():
    global is_processing

    is_processing = True
    socket_io.emit('agent_processing', {'processing': True})

    result = Welcomeagent.initiate_chat(
        manager,
        message="Welcome to SQL to Graph. What do you want to visualize today?"
    )
    messages = Welcomeagent.chat_messages[manager]

    is_processing = False
    socket_io.emit('agent_processing', {'processing': False})

    return jsonify(messages)

@app.route("/")
def index():
    return render_template('test1.html')

# Route to serve images as base64-encoded data


IMAGES_FOLDER = 'C:\\Users\\Pushpendra Singh\\Desktop\\AutoGen\\Localdir'

@app.route('/images/<filename>')
def get_image(filename,pocid):
    image_path = os.path.join(IMAGES_FOLDER, filename)
    image_format = 'png'

    try:
        # Open the image file in binary mode and encode it to base64
        with open(image_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode('utf-8')

        # Return the base64 encoded image along with its format
        return jsonify({'image': encoded_image, 'format': image_format})

    except Exception as e:
        print(f"Error while reading image: {str(e)}")
        return jsonify({'error': str(e)}), 400

def watch_folder():
    seen_files = set()
    
    while True:
        files = set(os.listdir(IMAGES_FOLDER))
        new_files = files - seen_files
        
        for new_file in new_files:
            file_path = os.path.join(IMAGES_FOLDER, new_file)
            
            # Check for image files
            if new_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                print(f"New image file detected: {new_file}")
                
                try:
                    with open(file_path, "rb") as img_file:
                        encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
                    socket_io.emit('new_image', {'image': encoded_image, 'format': 'png'})
                except Exception as e:
                    print(f"Error encoding image: {e}")
            
            # Check for CSV files
            elif new_file.lower().endswith('.csv'):
                print(f"New CSV file detected: {new_file}")
                
                try:
                    # Read CSV file and process it
                    with open(file_path, mode='r', newline='', encoding='utf-8') as csv_file:
                        reader = csv.DictReader(csv_file)
                        rows = [row for row in reader]  

                    # Emit CSV data to frontend
                    socket_io.emit('new_csv', {'data': rows})
                except Exception as e:
                    print(f"Error reading CSV file: {e}")

        seen_files = files
        time.sleep(1)  


@app.before_first_request
def start_folder_watch():
    thread = threading.Thread(target=watch_folder)
    thread.daemon = True
    thread.start()

app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    
    socket_io.run(app, debug=True, use_reloader=False, port=8080,host="0.0.0.0")
















