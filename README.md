# LangGraph Email Support Agent

A stateful Email Support Agent built using Python, LangGraph, LangChain, and Ollama Cloud.

This project was developed while studying LangGraph Essentials during my work and learning journey at 7Bots.ai. It demonstrates how LangGraph can be used to organize an AI application using shared state, nodes, edges, parallel execution, conditional routing, memory, and human-in-the-loop approval.

## Project Overview

The agent processes incoming customer emails through a structured workflow.

It can:

- Read incoming email information.
- Classify the email using an LLM.
- Identify the email intent, urgency, topic, and summary.
- Search simulated knowledge-base information.
- Create a unique support ticket reference.
- Generate a professional response.
- Route sensitive emails for human review.
- Send low-risk responses directly.
- Pause and resume workflows using LangGraph memory.

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
