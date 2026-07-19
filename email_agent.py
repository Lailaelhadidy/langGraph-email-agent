import os  
import json
import uuid # creates unique Ids
from typing import Literal, TypedDict 
from dotenv import load_dotenv # load variables from .env file
from langchain_ollama import ChatOllama # connects the application to ollama language model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

load_dotenv() # load varibale of .env file

# configure ollama cloud
api_key= os.getenv("OLLAMA_API_KEY")
model_name= os.getenv(
    "OLLAMA_MODEL",
    "gpt-oss:120b"
)
if not api_key:
    raise ValueError("Ollama API_KEY was not found in the .env file..")

llm = ChatOllama(
    model=model_name,
    base_url="https://ollama.com",
    temperature=0,
    reasoning="low",
    num_predict=512,
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
)

# Define the schemas 
class EmailClassification(BaseModel):

    intent: Literal[
        "question",
        "bug",
        "billing",
        "feature",
        "complex"
    ] = Field(description="The main purpose of the email")

    urgency: Literal[
        "low",
        "medium",
        "high",
        "critical"
    ] = Field(description="How urgently the email must be handled")

    topic: str = Field(description="The main topic of the email")
    summary: str = Field(description="A brief summary of the email")

class EmailAgentState(TypedDict):

    email_content: str
    sender_email: str
    email_id: str # unique identifier of the received message

    classification: dict | None # nested schema and this analysis is made by the llm
    ticket_id: str | None # a unique email tracking id
    search_results: list[str] | None 
    customer_history: dict | None #  Previous information stored about the customer

    draft_response: str | None # generated response by the llm 

def read_email(state: EmailAgentState) -> dict: 
    print( f"\n Reading email: {state['email_id']}")
    return {} # it doesnt add new data yet

def classify_intent(state: EmailAgentState) -> dict:

    classification_prompt = f"""
    Analyze this customer email.

    Email:
    {state['email_content']}

    Sender:
    {state['sender_email']}

    Return ONLY one valid JSON object.
    Do not use Markdown, bullet points, or explanations.

    Use exactly these keys:
    - intent
    - urgency
    - topic
    - summary

    Allowed intent values:
    question, bug, billing, feature, complex

    Allowed urgency values:
    low, medium, high, critical

    Example format:
    {{
        "intent": "billing",
        "urgency": "high",
        "topic": "duplicate subscription charge",
        "summary": "The customer reports being charged twice."
    }}
    """

    response = llm.invoke(classification_prompt) # sends the prompt to the model and returns a LangChain message object, commonly an AIMessage that is stored in response.content
    raw_text = response.content.strip() # removes extra spaces and blank lines from the beginning and end of the content

    # Remove a Markdown JSON block if the model adds one.
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "")
        raw_text = raw_text.replace("```", "")
        raw_text = raw_text.strip()

    
    try:
        final_classification = json.loads(raw_text) # convert json text into a Python dictionary

    except json.JSONDecodeError: # this runs when the model does not return valid JSON.
        raise ValueError(
            "The model did not return valid JSON.\n"
            f"Model response:\n{response.content}"
        )
    return { "classification": final_classification}

def search_documentation(state: EmailAgentState) -> dict:

    classification= state.get('classification', {}) #.get retrieve the key to get the data by key and if it doe not exist it returns {}
    query = (
    f"{classification.get('intent', '')} "
    f"{classification.get('topic', '')}"
    ).strip()

    print(f"Searching documentation with query: {query}")
    try:
        search_results = [
        "Duplicate charges should be reviewed by billing.",
        "Refunds may take up to five business days.",
        "Give the customer their support ticket ID."
    ]
    except Exception as e:
        search_results = [f"Search unavailable: {str(e)}"]
    return {"search_results": search_results}

def bug_tracking(state: EmailAgentState) -> dict:
    
    ticket_id = f"BUG_{uuid.uuid4()}"
    #uuid.uuid4() generates a highly unique identifier: BUG_3d621dcc-e569-4de2-b847-958c18f41c3b
    return {"ticket_id": ticket_id}

def write_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    
    classification= state.get('classification', {})
    context_sections= []
    if state.get('search_results'):
        formatted_docs = "\n".join([f"- {doc}" for doc in state['search_results']])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")
    if state.get('customer_history'):
        formatted_history = "\n".join([f"- {key}: {value}" for key, value in state['customer_history'].items()])
        context_sections.append(f"Customer history:\n{formatted_history}")  
    
    draft_prompt = f"""
    Draft a response to this customer email:
    {state['email_content']}

    Email intent: {classification.get('intent', 'unknown')}
    Urgency level: {classification.get('urgency', 'medium')}

    {chr(10).join(context_sections)}

    Guidelines:
    - Be professional and helpful
    - Address their specific concern
    - Use the provided documentation when relevant
    - Be brief
    """

    response = llm.invoke(draft_prompt) # It returns a LangChain message object, commonly an AIMessage
    # so reponse text is stored in: response.content
    
    # Determine if human review is needed based on urgency and intent
    needs_review = ( # Boolean variable returns true/false
        classification.get('urgency') in ['high', 'critical'] or
        classification.get('intent') == 'complex'
    )

    # Route to the appropriate next node
    if needs_review:
        goto = "human_review"
        print("Needs approval")
    else:
        goto = "send_reply"

    return Command(
        update = {"draft_response": response.content},
        goto = goto
    )

def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    """Pause for human review using interrupt and route based on decision"""

    classification = state.get('classification', {})

    # Interrupt() must come first - any code before it will re-run on resume
    human_decision = interrupt({
        "email_id": state['email_id'],
        "original_email": state['email_content'],
        "draft_response": state.get('draft_response', ""),
        "urgency": classification.get('urgency'),
        "intent": classification.get('intent'),
        "action": "Please review and approve/edit this response"
    })

    # Now process the human's decision
    if human_decision.get("approved"):
        return Command(
            update = {"draft_response": human_decision.get("edited_response", state['draft_response'])},
            goto = "send_reply"
        )
    else:
        # Rejection means human will handle directly
        return Command(update = {}, goto = END)

def send_reply(state: EmailAgentState) -> dict:
    """Send the email response"""
    # Integrate with a email service
    print(f"Sending reply: {state['draft_response'][:60]}...")
    return {}

# Create the graph
builder = StateGraph(EmailAgentState)

# Add nodes
builder.add_node("read_email", read_email)
builder.add_node("classify_intent", classify_intent)
builder.add_node("search_documentation", search_documentation)
builder.add_node("bug_tracking", bug_tracking)
builder.add_node("write_response", write_response)
builder.add_node("human_review", human_review)
builder.add_node("send_reply", send_reply)

# Add edges
builder.add_edge(START, "read_email")
builder.add_edge("read_email", "classify_intent")
builder.add_edge("classify_intent", "search_documentation")
builder.add_edge("classify_intent", "bug_tracking")
builder.add_edge("search_documentation", "write_response")
builder.add_edge("bug_tracking", "write_response")
builder.add_edge("send_reply", END)

# Compile with checkpointer for persistence
memory = InMemorySaver()
app = builder.compile(checkpointer = memory)

def main() -> None:
    initial_state: EmailAgentState = {
        "email_content": (
            "I was charged twice for my "
            "subscription. Please help urgently."
        ),
        "sender_email": "customer@example.com",
        "email_id": "email-001"
    }

    config = {"configurable": {"thread_id": "email-001"}}

    result = app.invoke(initial_state, config )

    if "__interrupt__" in result:
        interrupt_data = (
            result["__interrupt__"][-1].value
        )

        print("\nHuman review required:")
        print(interrupt_data)

        approve = input(
           "\nApprove response? yes/no: "
        ).strip().lower()

        if approve == "yes":
            edited_response = input(
                "Enter an edited response, "
                "or press Enter to keep the draft: "
            ).strip()

            decision = {
                "approved": True
            }

            if edited_response:
                decision["edited_response"] = (
                    edited_response
                )

        else:
            decision = {
                "approved": False
            }

        final_result = app.invoke(
            Command(resume=decision),
            config
        )

        print("\nFinal state:")
        print(final_result)

    else:
        print("\nWorkflow finished directly.")
        print(result)

if __name__ == "__main__":
    main()