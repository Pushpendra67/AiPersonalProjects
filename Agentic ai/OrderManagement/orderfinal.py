
import json
import autogen
import os
from autogen import ConversableAgent

# LLM Configuration for Azure OpenAI
llm_config = { 
    "config_list": [ 
        { 
            "model": "gpt-4", 
            "api_key": "***", 
            "base_url": "***", 
            "api_version": "2023-03-15-preview", 
            "api_type": "azure" ,
            "cache_seed": None
        } 
    ] 
}

import json

# Load the product details from the JSON file
def load_product_list(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['products']

# Path to the JSON file
product_list = load_product_list('product_list.json')

# Convert product list to a string that can be used in the system message
product_list_str = json.dumps(product_list, indent=4)

# Modify the agent's configuration to dynamically load the product list
ProductShowingAgent = autogen.AssistantAgent(
    name="ProductShowingAgent",
    human_input_mode="NEVER",
    system_message=f"""You are responsible for showing products available in the store. 
                      Provide product details such as price, discount, and expiry date from the given product list: {product_list_str}""",
    llm_config=llm_config
)

OrderProcessingAgent = autogen.AssistantAgent(
    name="OrderProcessingAgent",
     human_input_mode="NEVER",
    #  llm_config=False,
    system_message="""You are responsible for processing customer orders. 
                      Ask for payment details, apply discounts, and confirm the order after successful payment.""",
    llm_config=llm_config,
)

DeliveryAgent = autogen.AssistantAgent(
    name="DeliveryAgent",
     human_input_mode="NEVER",
    system_message="""You are responsible for managing deliveries. 
                      Ask for the customer's delivery address, inform about delivery charges, and confirm delivery after payment.""",
    llm_config=llm_config,
)

FeedbackAgent = autogen.AssistantAgent(
    name="FeedbackAgent",
    system_message="""You are responsible for collecting feedback from customers about their order and delivery experience.""",
    llm_config=llm_config,
     human_input_mode="NEVER"
)
ProductShowingAgentinput = ConversableAgent(
    name="ProductShowingAgentinput",
    llm_config=False, 
    human_input_mode="ALWAYS",  
)

OrderProcessingAgentinput = ConversableAgent(
    name="OrderProcessingAgentinput",
    llm_config=False,  
    human_input_mode="ALWAYS",  
)

DeliveryAgentinput = ConversableAgent(
    name="DeliveryAgentinput",
    llm_config=False,  
    human_input_mode="ALWAYS",
      description="" 
)



# Define the human interaction agent with a valid name
FeedbackAgentinput = ConversableAgent(
    name="FeedbackAgentinput",
    llm_config=False,  # no LLM used for human proxy
    human_input_mode="ALWAYS",  
)
HumanProxy = ConversableAgent(
    name="HumanProxy",
    llm_config=False, 
    human_input_mode="ALWAYS",  
)

# ---------------------------------custom method for agent selection ---->

# agents = [HumanProxy,ProductShowingAgent, ProductShowingAgentinput, OrderProcessingAgent, OrderProcessingAgentinput, DeliveryAgent, DeliveryAgentinput, FeedbackAgent, FeedbackAgentinput]

# def custom_speaker_selection(last_speaker, groupchat):
#     """
#     Custom speaker selection function.
    
#     Parameters:
#     - last_speaker: Agent - The last agent who spoke.
#     - groupchat: GroupChat - The current group chat object.
    
#     Returns:
#     - The Agent who should speak next.
#     """
  
#     #print("this si last speaker-->",groupchat)
#     # Get the index of the last speaker
#     last_speaker_index = groupchat.agents.index(last_speaker)
  

    
#     # Determine the next speaker index
#     next_speaker_index = (last_speaker_index + 1) % len(groupchat.agents)
    
#     return groupchat.agents[next_speaker_index]


# -------------------------------------------------------------------------------------------------


# Define group chat with agents
groupchat = autogen.GroupChat(
   
  agents = [HumanProxy,ProductShowingAgent, ProductShowingAgentinput, OrderProcessingAgent, OrderProcessingAgentinput, DeliveryAgent, DeliveryAgentinput, FeedbackAgent, FeedbackAgentinput],
    speaker_selection_method="round_robin",
    # speaker_selection_method=custom_speaker_selection,
    messages=[]
)
print("this is groupchat-->",groupchat)

# Define group chat manager
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    code_execution_config={"use_docker": False},
    llm_config=llm_config,
    is_termination_msg=lambda msg: "TERMINATE" in str(msg.get("content", ""))
)

# Function to simulate the chat process
result = HumanProxy.initiate_chat(
    manager, 
    message="""Hello, I'd like to see all the products available in the store."""
)




