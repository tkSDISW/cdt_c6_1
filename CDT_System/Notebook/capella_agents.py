from pathlib import Path
import os
import yaml
import capellambse
import capellambse.decl as decl
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableLambda
import re
import csv
from jinja2 import Template


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

class CapellaModelUpdater:
    def __init__(self, model, debug=False):
        """
        Initialize the Capella model updater.
        
        :param model: An instance of capellambse.MelodyModel.
        :param debug: Boolean flag to enable LangChain debug mode.
        """
        self.model = model
        self.debug = debug

        # Initialize LangChain for YAML validation with debug mode

        os.environ["OPENAI_API_KEY"] = get_api_key()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    def test_llm(self):
        """Test if the LLM is working by sending a simple prompt."""
        try:
            test_prompt = "Hello! Can you confirm that the LLM is working?"
            response = self.llm.invoke(test_prompt)
            
           # Extract only the response content
            llm_content = response.content if hasattr(response, "content") else str(response)
    
            if self.debug:
                print("\n🔹 LLM Test Response:")
                print(llm_content)  # Print only the content
    
            return llm_content
        except Exception as e:
            print("\n❌ Error: LLM is not responding.")
            print(e)
            return None
    
     
    @tool
    def verify_yaml(yaml_content: str) -> str:
        """Validates and corrects YAML content before applying updates."""
        try:
            data = yaml.safe_load(yaml_content)
            if "name" not in data or not isinstance(data["name"], str):
                data["name"] = "Unnamed Component"
            return yaml.dump(data, default_flow_style=False)
        except yaml.YAMLError as e:
            return f"Error in YAML format: {str(e)}"


    def generate_description(self, yaml_content):
        """Use LangChain to generate missing descriptions."""
        prompt = f"""
        The following is a YAML representation of a system component:
        ---
        {yaml_content}
        ---
        If the description field is missing or too short, generate a meaningful description
        based on the component's name and other attributes.
        """
        
        chain = self.llm | RunnableLambda(self.verify_yaml)
        response = chain.invoke(prompt)

        if self.debug:
            print("Generated Description:", response.contemt)  # Debug output
        
        return response


    def extract_uuids_from_csv(self, filename):
        """Read a CSV file and extract a list of UUIDs from the 'uuid' column."""
        uuids = []
    
        try:
            with open(filename, "r", newline="") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
    
                # Extract UUIDs from the second column
                for row in reader:
                    if len(row) > 1:  # Ensure row has at least 2 columns
                        uuids.append(row[1])  # UUID is in the second column
    
            print(f"✅ Extracted {len(uuids)} UUIDs from '{filename}'.")
        except FileNotFoundError:
            print(f"❌ Error: The file '{filename}' was not found.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

        return uuids
    
    def remove_component(self, component):
        """Remove a component from a given parent."""
        import io
        import yaml
        from jinja2 import Template
        from capellambse import decl
    
        # Define YAML constructors for custom tags
        def uuid_constructor(loader, node):
            return loader.construct_scalar(node)
    
        def promise_id_constructor(loader, node):
            return loader.construct_scalar(node)
    
        def promise_constructor(loader, node):
            return loader.construct_scalar(node)
    
        # Register constructors
        yaml.add_constructor("!uuid", uuid_constructor, Loader=yaml.SafeLoader)
        yaml.add_constructor("!promise", promise_constructor, Loader=yaml.SafeLoader)
        yaml.add_constructor("promise_id", promise_id_constructor, Loader=yaml.SafeLoader)
    
        # Corrected YAML string (proper indentation & colon)
        yaml_template = """
- parent: !uuid {{ parent_uuid }}
  delete:
    components:
      - !uuid {{ uuid }}
"""
    
        # Render YAML with Jinja2
        data = {
            "parent_uuid": component.parent.uuid if component.parent else None,
            "uuid": component.uuid,
        }
        template = Template(yaml_template)
        self.yaml_content = template.render(data)
    
        try:
            # Validate rendered YAML (not the template string!)
            yaml_content = yaml.safe_load(self.yaml_content)
            print("✅ YAML validated successfully!")
            component_name = component.name
            component_uuid = component.uuid
            parent_uuid = component.parent.uuid
            parent_name =component.parent.name
            print(self.yaml_content)
            # Apply YAML update to Capella model
            decl.apply(self.model, io.StringIO(self.yaml_content))
            print("✅ Model update applied successfully.")

            # Debugging information before applying
            if self.debug:
                print(f"Removed component {component_name} : {component_uuid} "
                      f"from parent {parent_name} : { parent_uuid}.")
            # Save model after modification
            self.model.save()
            return yaml_content  # Return parsed content if needed
    
        except yaml.YAMLError as e:
            print(f"❌ YAML validation error: {e}\nProblematic YAML:\n {self.yaml_content}")
            return None  # Return None instead of breaking execution
    
        except Exception as e:
            raise RuntimeError(f"❌ YAML Application Error: {e}")

    def generate_file(self, yaml_content, prompt, filename):
        """Use LangChain to generate a CSV file from AI response."""
    
        response = self.llm.invoke(prompt)
    
        if self.debug:
            print("Processed Response:", response.content)  # Debug output
    
        # Extract CSV content using improved regex
        csv_match = re.search(r"```csv\s*(.*?)\s*```", response.content, re.DOTALL)
    
        if csv_match:
            csv_data = csv_match.group(1)  # Extract the CSV text
    
            # Convert CSV text to a list of rows
            rows = [line.split(",") for line in csv_data.strip().split("\n")]
    
            # Save to a .csv file
            with open(filename, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(rows)
    
            print(f"✅ CSV file '{filename}' has been created successfully.")
        else:
            print("❌ No valid CSV content found in the response.")
    
        return response

        
 


    def add_component(self, parent_uuid, component_name, description=""):
        """Add a new component to a given parent."""
        add_command = decl.Extend(
            parent=f"!uuid {parent_uuid}",
            extend={
                "functions": [
                    {"name": component_name, "description": description}
                ]
            }
        )
        self.model.apply(add_command)
        
        if self.debug:
            print(f"Added component '{component_name}' under parent {parent_uuid}.")  # Debug output
        
        #self.model.save()