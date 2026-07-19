````markdown
# LangGraph Email Support Agent

A stateful email-support workflow built with **Python, LangGraph, LangChain, and Ollama Cloud**.

This project was developed during my Agentic AI learning journey at **7Bots.ai** after completing the **LangGraph Essentials** course by LangChain Academy.

The application reads a customer email, classifies it, searches relevant support information, creates a tracking ticket, drafts a response, and decides whether the reply can be sent directly or requires human approval.

---

## Project Overview

The Email Support Agent demonstrates how LangGraph can organize an AI workflow using:

- Shared graph state
- Nodes and edges
- Parallel execution
- Conditional routing
- LLM-based classification
- Checkpoint memory
- Human-in-the-loop approval
- Workflow interruption and resumption

The LLM handles semantic tasks such as email classification and response generation, while LangGraph manages the workflow, state updates, execution order, memory, and routing.

---

## Workflow

```text
START
  ↓
Read Email
  ↓
Classify Intent
  ├──────────────────────┐
  ↓                      ↓
Search Documentation   Create Ticket
  └───────────┬──────────┘
              ↓
        Write Response
          ├──────────────┐
          ↓              ↓
     Human Review     Send Reply
       ├──────┐           ↓
       ↓      ↓           END
 Send Reply  END
       ↓
      END
````

### Workflow Steps

1. **Read Email**
   Receives the email content, sender address, and email ID.

2. **Classify Intent**
   Uses the LLM to identify:

   * Intent: question, bug, billing, feature, or complex
   * Urgency: low, medium, high, or critical
   * Topic
   * Summary

3. **Parallel Processing**
   Two independent nodes run in parallel:

   * Search Documentation
   * Create Tracking Ticket

4. **Write Response**
   Uses the email classification and search results to generate a professional reply.

5. **Conditional Routing**
   High, critical, or complex emails are sent to human review. Other emails are sent directly.

6. **Human Review**
   The reviewer can:

   * Approve the draft
   * Edit and approve it
   * Reject it and handle the email manually

7. **Send Reply**
   Simulates sending the approved response.

---

## LangGraph Concepts Used

### State

`EmailAgentState` stores all information shared between the nodes, including:

* Email content
* Sender email
* Email ID
* Classification
* Ticket ID
* Search results
* Customer history
* Draft response

Each node returns only the state fields it changes. LangGraph automatically merges those updates into the shared state.

### Nodes

Each node is a Python function responsible for one task, such as classification, documentation search, ticket creation, or response generation.

### Static Edges

Static edges define workflow steps that always follow the same path.

### Parallel Execution

The documentation-search and ticket-creation nodes run in parallel because they are independent.

### Conditional Routing

The `write_response` node uses:

```python
Command(update=..., goto=...)
```

to update the state and choose between:

```text
human_review
send_reply
```

### Memory

`InMemorySaver` stores checkpoints during execution.

A unique `thread_id` identifies each workflow and allows an interrupted process to resume correctly.

### Human in the Loop

The application uses:

```python
interrupt(...)
```

to pause the graph for human approval.

It resumes using:

```python
Command(resume=decision)
```

with the same thread configuration.

---

## Technology Stack

* Python
* LangGraph
* LangChain
* Ollama Cloud
* ChatOllama
* uv
* python-dotenv

---

## Project Structure

```text
langgraph-email-agent/
│
├── email_agent.py
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
└── uv.lock
```

---

## Requirements

Before running the project, install:

* Python 3.12 or later
* uv
* Git
* An Ollama Cloud account and API key

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/langgraph-email-agent.git
cd langgraph-email-agent
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Install the dependencies

```bash
uv sync
```

When starting without an existing project environment, use:

```bash
uv init
uv add python-dotenv langchain-ollama langgraph
```

## Environment Configuration

Create a file named:.env
Add:
```env
OLLAMA_API_KEY=your_ollama_api_key
OLLAMA_MODEL=your_available_ollama_model
```


## Running the Application
Run the project from the terminal:

```bash
uv run python email_agent.py
```
