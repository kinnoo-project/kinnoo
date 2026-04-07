## Project Vision and Overview
### Origin Story
Kinnoo is a platform where developers can publish and share their AI agents with other developers.

I came up with the idea of kinnoo after a conversation I had with my developer friend. He had been using AI agents to code for quite a few months already, and I was just getting started. I asked him if he could share his AI coding setup and his experience (conversation history) from working with the coding agents. This led me on a search to see if anyone had built a general way for developers to share their AI agents with others.

At the same time, I wanted to start to build my own AI agents to do various things. My requirements were that:
1. My agents can be run from the command-line
2. My agent development is not tied to a specific framework. I want flexibility.
3. I still use Github to version control my code, but I want an easy way to "ship" a version of my agent every time I make an incremental build.
4. I want it to be easy for my friend (and anyone else) to be able to install my shipped agent, and run it themselves - without having to go to my codebase, read install docs, etc.

I did a bit of research, and couldn't find anything else out there that really appealed to me. So I decided to build something myself. And so Kinnoo was born.

The name Kinnoo came from a back-and-forth LLM conversation on a catchy name for an agent CLI tool that didn't conflict with anything else. There were other names that the LLM suggested that started with "kin" and I liked this because it conveys the notion of a community. After a few permutations, I landed on kinnoo. I also liked that it was an alternate spelling for a type of fruit (variant of a mandarin orange).

### Vision
The vision is that kinnoo will be the de facto packaging and distribution standard for CLI-runnable AI agents, in sort of the same way that pip is the standard for Python applications, and npm for JS/TS applications.

I do plan to support UI-based agents (where the input is through a Chat app), but the vision is to support modular and composable agents, especially for automation, CI/CD, and reproducibility, through the kinnoo CLI. In this way, kinnoo's main focus is to support agents whose inputs and outputs are through the command line.

I plan to support the most common agent frameworks - LangChain / LangGraph, OpenAI Agent SDK, PydanticAI, CrewAI, smolagents. For OpenClaw, I plan to support skills that can be run via the command line.

By CLI-runnable, I mean that Kinnoo expects your agent to have a clear entrypoint script, a parseable input type (either a string, JSON or well-defined arg:value pairs), and a defined, parseable output type.

The kinnoo CLI will provide an extensive suite of commands for working with your AI agents. The general flow is:

```
Agent Developer:

kinnoo init / kinnoo import  (initialize an agent, or import an existing agent)
           |
  (do some development) <--------------
           |                          |
kinnoo test / kinnoo run   (test and run your agent)
           |
kinnoo pack / kinnoo publish (version, package and publish your agent to the registry)


Agent End-User:

kinnoo install  (install an agent from the registry)
           |
kinnoo run  (run the agent)
```

Kinnoo will prioritize security and privacy, ensuring that humans are always in the loop, and agents and their data are protected from unauthorized access or misuse. Security features include signed artifacts, provenance-aware metadata, safe execution defaults, preflight checks, and human-in-the-loop controls for sensitive actions.

I have a lot of engineering experience but it's mostly as a technical project manager. I still consider myself a mediocre developer at best, so I can't do this alone. Since kinnoo is entirely open source, I invite the community to contribute and make this vision happen. I'm learning a lot as I go through this project, and look forward to learning with the rest of the developer community on this.
