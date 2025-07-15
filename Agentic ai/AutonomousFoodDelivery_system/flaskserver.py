# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from SocketConsole import SocketIOConsole
import os
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.agents import CodeExecutorAgent, UserProxyAgent
# Load environment variables
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Azure OpenAI client
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("api_version")
api_key = os.getenv("OPENAI_API_KEY")

model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o",
    azure_endpoint=azure_endpoint,
    model="gpt-4o",
    api_version=api_version,
    api_key=api_key,
)

# Custom Console class to emit messages via Socket.IO
# class SocketConsole:
#     def __init__(self, socket):
#         self.socket = socket

#     async def __call__(self, message):
#         if isinstance(message, str):
#             self.socket.emit('message', {'data': message})
#         else:
#             self.socket.emit('message', {'data': str(message)})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_message(data):
    task = data['message']
    
    async def process_task():
        surfer = MultimodalWebSurfer(
            "WebSurfer",
            model_client=model_client,
        )

        assistant = AssistantAgent(
        "Assistant",
        model_client=model_client,
        )


        fileSurfer = FileSurfer("FileSurfer", model_client=model_client)
        # ws = MultimodalWebSurfer("WebSurfer", model_client=client)
        Coder = MagenticOneCoderAgent("Coder", model_client=model_client)
        Executor = CodeExecutorAgent("Executor", code_executor=LocalCommandLineCodeExecutor())



        team = MagenticOneGroupChat([surfer,assistant,fileSurfer,Coder,Executor], model_client=model_client)
        
        console = SocketIOConsole(socketio)
        await console(team.run_stream(task=task))

    # Run the async task
    asyncio.run(process_task())

if __name__ == '__main__':
    socketio.run(app, debug=True,use_reloader=True)