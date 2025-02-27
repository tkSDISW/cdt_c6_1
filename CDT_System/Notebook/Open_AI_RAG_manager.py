import sys
from pathlib import Path
from openai import OpenAI
from IPython.display import display, Markdown
from IPython.core.display import HTML
from ipywidgets import widgets
import numpy as np
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import asyncio
from ipywidgets import widgets
from IPython.display import display

def get_api_key():
    """Retrieve the OpenAI API key from a hidden file."""
    home_dir = Path.home()
    key_file = home_dir / ".secrets" / "openai_api_key.txt"

    if not key_file.exists():
        raise FileNotFoundError(
            f"API Key file not found at {key_file}. "
            "Please ensure the key is saved correctly."
        )

    with key_file.open("r") as f:
        api_key = f.read().strip()

    if not api_key:
        raise ValueError("API Key file is empty. Provide a valid API key.")

    return api_key


class EmbeddingManager :
    def __init__(self):
        """Initialize the analyzer with YAML content."""
        try:
            self.api_key = get_api_key()
            print("OpenAI API Key retrieved successfully.")
        except (FileNotFoundError, ValueError) as e:
            print(e)
            sys.exit(1)  # Exit with an error code

       
        self.client = OpenAI(
            api_key=self.api_key,  # This is the default and can be omitted
            )
        self.model = "text-embedding-3-small"
        self.model_file = ''
        self.embedding_file =''
    
        
    def save_embeddings(self ):
        """Save embeddings to a file."""
        with open(self.embedding_file, "w") as f:
            json.dump(self.embeddings, f)

    def set_files(self, model_file, embedding_file) :
        """Set model file and ebedding fie."""
        self.model_file = model_file
        self.embedding_file = embedding_file


    def is_embedding_up_to_date(self):
        """Check if the embedding file is up-to-date with the model file."""
        if not os.path.exists(self.embedding_file):
            # Return False if the embedding file is not present
            print("Embedding file not found.")
            return False
        model_time = os.path.getmtime(self.model_file)
        embedding_time = os.path.getmtime(self.embedding_file)
        #print("embedding time:",embedding_time, "model time:", model_time) 
        return embedding_time > model_time
    
    def generate_object_embeddings(self, objects):
        for obj in objects:
            # Combine metadata into a single text string
            metadata_text = f"{obj['name']} {obj['type']} {obj['phase']} {obj['source_component']} {obj['target_component']}"
            metadata_text =  metadata_text.replace("\n", " ")
            obj["embedding"] = self.client.embeddings.create(input = [metadata_text], model=self.model).data[0].embedding
        self.embeddings = objects
        return objects

    def create_model_embeddings(self, model) :
        
        def get_object_info(object, phase ) :
            object_info = {
                    "uuid": object.uuid,
                    "name": object.name,
                    "type": type(object).__name__,
                    "phase" : phase,
                    "source_component": "",
                    "target_component": "" 
                }
            return object_info
        def get_component_exchange_info(object, phase ) :
            object_info = {
                    "uuid": object.uuid,
                    "name": object.name,
                    "type": type(object).__name__,
                    "phase" : phase,
                    "source_component": obj.source.owner.name,
                    "target_component": obj.target.owner.name 
                }
            return object_info
            
        def add_unique_object(obj_list, new_obj):
            """
            Adds a new object to the list if its UUID is not already present.
        
            :param obj_list: List of existing objects.
            :param new_obj: Object to potentially add to the list.
            """
            if not any(obj.get('uuid') == new_obj.get('uuid') for obj in obj_list):       
                obj_list.append(new_obj)

        if self.is_embedding_up_to_date() :
            print("Loading embeddings")
            self.load_embeddings()
        else : 
            print("Creating Embeddings")
            object_data = []
            #OA  
            phase = "Operational Analysis OA"
            for component in model.oa.all_entities:  
                object_info = get_object_info(component,phase)
                add_unique_object(object_data,object_info)
            for obj in model.oa.all_activities:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.oa.all_capabilities:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.oa.all_entity_exchanges:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.oa.all_processes:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            #SA
            phase = "System Analysis SA"
            for component in model.sa.all_components: 
                object_info = get_object_info(component,phase)
                add_unique_object(object_data,object_info)
            for obj in model.sa.all_capabilities:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.sa.all_function_exchanges:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.sa.all_functions:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.sa.all_missions:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.sa.all_functional_chains:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            #LA
            phase = "Logical Architecture LA"
            for obj in model.la.all_capabilities:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for component in model.la.all_components:  
                object_info = get_object_info(component,phase)
                add_unique_object(object_data,object_info)
            for obj in model.la.all_functions:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.la.all_functional_chains:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.la.all_interfaces:  
                object_info =  get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.la.component_exchanges:  
                object_info =  get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.la.actor_exchanges:  
                object_info =  get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            #PA
            phase = "Physical Architecture PA"
            for component in model.pa.all_components:  
                object_info = get_object_info(component,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_functions:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_functional_chains:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_capabilities:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_component_exchanges:  
                object_info = get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_physical_exchanges:  
                object_info = get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_physical_links:  
                object_info = get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_physical_paths:  
                object_info = get_object_info(obj,phase)
                add_unique_object(object_data,object_info)
            for obj in model.pa.all_physical_exchanges:  
                object_info = get_component_exchange_info(obj,phase)
                add_unique_object(object_data,object_info)
            model_embeddings = self.generate_object_embeddings(object_data)
            
            print("Saving embeddings")
            self.save_embeddings()



    
    def load_embeddings(self):
        """Load embeddings from a file."""
        with open(self.embedding_file, "r") as f:
            self.embeddings = json.load(f)

    # Define a cosine similarity function
    def cosine_similarity(self, vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    # Find similar objects based on the query
    def find_similar_objects(self, query,  top_n=10):
        query_embedding = self.client.embeddings.create(input = [query], model=self.model).data[0].embedding
        similarities = []
        
        for obj in self.embeddings:
            similarity = self.cosine_similarity(query_embedding, obj["embedding"])
            similarities.append((obj, similarity))
        
        # Sort by similarity in descending order
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    
def interactive_query_and_selection(model_embedding_manager):
    """
    Interactive function to query objects, review responses, and select indices for further processing.
    
    :param model_embedding_manager: The manager object to handle embedding and similarity queries.
    :return: List of selected objects based on indices.
    """
    while True:
        # Step 1: Prompt for query
        query = input("Enter query for objects to be analyzed: ")

        # Step 2: Filter and rank objects
        ranked_objects = model_embedding_manager.find_similar_objects(query)

        # Step 3: Display ranked objects
        print("\nThis is a list of ranked Objects Based on Query:")
        for i, (obj, similarity) in enumerate(ranked_objects):
            print(f"Index: {i}, Name: {obj['name']}, Similarity: {similarity:.2f}, "
                  f"Type: {obj['type']},Phase: {obj['phase']}, Source: {obj.get('source_component', 'N/A')}, "
                  f"Target: {obj.get('target_component', 'N/A')}")

        # Step 4: Ask for user action
        user_input = input("\nEnter the indices of the selected objects (comma-separated), or any non-integer input to retry: ")

        # Check if the input contains only integers
        if not all(part.strip().isdigit() for part in user_input.split(",")):
            # Retry if any non-integer input is detected
            print("\nNon-integer input detected. Retrying with a new query.")
            continue

        try:
            # Parse selected indices
            selected_indices = [int(i.strip()) for i in user_input.split(",")]
            selected_objects = [ranked_objects[i][0] for i in selected_indices]
            #print("\nSelected Objects:")
            #for obj in selected_objects:
            #    print(f"Name: {obj['name']}, Type: {obj['type']}")
            return selected_objects
        except (ValueError, IndexError):
            # Handle invalid input
            print("\nInvalid input. Please enter valid indices or retry.")




class ChatGPTAnalyzer:
    def __init__(self, yaml_content):
        """Initialize the analyzer with YAML content."""
        try:
            self.api_key = get_api_key()
            print("OpenAI API Key retrieved successfully.")
        except (FileNotFoundError, ValueError) as e:
            print(e)
            sys.exit(1)  # Exit with an error code

        self.yaml_content = yaml_content
        self.messages = [
            {
                "role": "system",
                "content": f"You are an expert in analyzing YAML files for system design. Here is the YAML file:\n---\n{self.yaml_content}\n---",
            }
        ]

    def _construct_prompt(self, user_prompt):
        """Construct the full prompt with YAML content."""
        return f"""
The following is a YAML file describing a system design component in Capella:
---
{self.yaml_content}
---
{user_prompt}
Please format the response in .html format.
"""

    def initial_prompt(self, user_prompt):
        """Set the initial user prompt in the conversation."""
        user_prompt = user_prompt + " Format the response in .html format."
        self.messages.append({"role": "user", "content": user_prompt})

    def follow_up_prompt(self, user_prompt):
        """Add a follow-up prompt continuing the conversation."""
        self.messages.append({"role": "user", "content": user_prompt})

    def get_response(self):
        """Send messages to ChatGPT and get a response."""
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                messages=self.messages,
                model="gpt-4o",
            )
            assistant_message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_message})

            soup = BeautifulSoup(assistant_message, "html.parser")

            # Remove <script> and <style> tags
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Render the cleaned HTML
            assistant_message = str(soup)
            return assistant_message

        except Exception as e:
            return f"Error communicating with OpenAI API: {e}"

    def interactive_chat(self):
        """Start an interactive chat session."""
        print("Starting interactive chat...")
        while True:
            user_prompt = input("Enter your prompt (or type 'exit' to quit): ")

            if user_prompt.lower() == "exit":
                print("Exiting...")
                break

            self.follow_up_prompt(user_prompt)
            response = self.get_response()

            display(Markdown(f"**Your Prompt:**\n\n{user_prompt}\n"))
            if "<table" in response or "<html" in response:
                display(HTML(response))  # Render HTML
            else:
                display(Markdown(f"**ChatGPT Response:**\n\n{response}\n"))

