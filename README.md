# ArchDrift

> ArchDrift is a linter that compares the architecture diagrams in your repo (Mermaid, PNG or SVG) against your actual code, flags where they've drifted apart, and generates an updated Mermaid diagram to fix them.

## Team

**Team Name:** Quantum_Coders


| Member | Contribution   |
| ------ | -------------- |
| Raghunathan B K | Team Leader |
| Kaevin P | Member |
| Viswanath A G | Member |
| Sanjay Siddhakumar | Member |


## Problem Statement

### The Problem

Architecture diagrams are created once and rarely revised. Usually, the architecture diagram in the docs or README was correct at the time it was created. After that, the code has likely evolved - a service was split, a database switched, a cache introduced, an API endpoint renamed, etc. But the architecture diagram remains unchanged, and nothing in the development process evaluates the diagram.

Consequence 1: For new engineers and new contributors, the architecture diagram is a primary source for gaining insight into the system. If the architecture diagram is incorrect, new engineers and contributors will form an incorrect mental model of the system and either waste hours working on incorrect relationships or deploy changes based on non-existent relationships.

Consequence 2: Security personnel, auditors and reviewers all make judgments based on trust and data flow diagrams that may or may not reflect the current state of the system.

Consequence 3: Senior developers and maintainers end up as the human source of truth, explaining "ignore the diagram, it's outdated" again and again.

Consequence 4: Open-source projects lose potential contributors when the docs don't match the code.

### Why We Chose This Problem

A problem that everyone has encountered. Most engineers have at some point trusted a diagram within a README file and found that the actual implementation has changed from the diagram. This is something that occurs regularly, and no one owns the solution to it. Diagrams tend to become outdated, and teams will complain about this but rarely take action on it. Updating a diagram is a manual process, and no one tends to have a sense of urgency for it.
A gap in the existing tooling. We have testing, type checking, code analysis and CI for code. There is no similar tooling for documentation, particularly diagrams. This is an example of something that could be machine verified yet currently isn't.
This is now solvable with recent AI. Code is text-based, and diagrams are visual which made automation of this difficult previously. Multimodal AI can now interpret diagrams, whilst code analysis tools can extract the actual implementation of a system. By combining this we can move from "diagram drift" being an ambiguous issue to one that can be identified and surfaced with evidence by an automation tool.


## Solution

Support for finding diagrams (PNG, SVG, Mermaid)
Parse diagrams (Mermaid, SVG or image using a multimodal model) and extract a graph
Parse code (connection strings, imports, route definitions, Docker/Kubernetes configurations) and extract a graph
Compare the graphs and report differences in:
•	out-of-sync components
•	stale components
•	changed connections

Report drift with confidence and evidence, such as:

**"Diagram shows Auth → SQLite but routes via Redis at line v2/auth.py:42."**

Compare graphs and generate a new Mermaid diagram to replace the out-of-date diagram in the same pull request

Advantages:
•	Graph extraction is purely structural
•	Drift analysis is deterministic, and all reports are explainable
•	Can be run as an agent skill or CLI or as a GitHub Action
•	Out-of-date diagrams cause failures in CI like any other linting issue

### Key Features

- [Feature 1]
- [Feature 2]
- [Feature 3]
- [Feature 4]

## Innovation and Differentiation

[Explain what is innovative about the approach and how it differs from existing or conventional solutions.]

## Technical Implementation

### Architecture

[Add the system architecture or workflow Mermaid diagram here.]

### Technology Stack

| Category        | Technologies                |
| --------------- | --------------------------- |
| Frontend        | N/A for the core tool (CLI and CI output). Optional: a static HTML drift report      |
| Backend         | Python 3.11+, Typer (CLI), Pydantic (graph and finding schemas), NetworkX (graph diff), Python ast and tree-sitter (code analysis), PyYAML (Docker Compose and Kubernetes parsing)       |
| Database        | N/A. Graphs and reports are stored as JSON files       |
| AI / ML         | Gemma 4 (open-weight, multimodal) reads PNG/SVG diagrams and extracts nodes and edges as schema-constrained JSON. Served locally through Ollama, so the whole pipeline stays open-source |
| Infrastructure  | GitHub Actions (CI drift check on pull requests), Docker (packaged CLI), pre-commit hook, pytest      |
| APIs / Services | GitHub API (posts drift findings as PR comments), Mermaid CLI (mermaid-cli) to render and validate generated diagrams, agent skill interface           |


If a category or technology is not implemented in the project, specify `N/A` instead of leaving the field blank.

### How It Works

[Explain the major components of the system and how they interact.]

### Technical Decisions

[Explain important architectural, algorithmic, or engineering decisions made during development.]

## Implementation During the Hackathon

[Describe what the team built during the Hack Day and the major functionality or components completed during the event.]

### Team Contributions

- **[Member Name]:** [Contribution]
- **[Member Name]:** [Contribution]
- **[Member Name]:** [Contribution]
- **[Member Name]:** [Contribution]

## Working Application

**Live Application:** [Live URL]

[Briefly explain how the deployed application can be accessed and what functionality can be tested.]

The submitted application should be functional and accessible through the provided link where applicable.

## Demo Video

**Demo Video:** [Video URL]

[Provide a short demonstration of the working project, covering the main user flow and important functionality.]

## Open Source and AI Usage

### AI / Models

- **[Model]:** [How it is used]

### Open Source Components

- **[Library / Framework]:** [Purpose]
- **[Dataset]:** [Purpose]
- **[API / Service]:** [Purpose]

[Include relevant licenses, attribution, and acknowledgements for external components.]

## Setup and Usage

### Prerequisites

- [Requirement]
- [Requirement]

### Installation

```bash
git clone [repository-url]
cd [project-directory]
[installation-command]
```

### Environment Variables

```env
[VARIABLE_NAME]=[value]
```



### Running the Project

```bash
[run-command]
```

### Usage

[Explain the basic steps required to use the project.]

## Devpost Submission

**Devpost Project:** [Devpost Project URL]

[Add the link to the team's Devpost submission. Ensure the Devpost project page is complete and contains the required project information, links, media, and team details.]

## Credits and License

### Credits

[Credit libraries, frameworks, datasets, models, APIs, contributors, and other external resources used.]

### License

[License name and/or link.]

## Submission Checklist

- [ ] Project title and description added
- [ ] All team members listed
- [ ] Problem clearly explained
- [ ] Reason for choosing the problem explained
- [ ] Solution and key features documented
- [ ] Innovation and differentiation explained
- [ ] Architecture included
- [ ] Technical implementation documented
- [ ] Work completed during the hackathon documented
- [ ] Team contributions documented
- [ ] Working application is functional
- [ ] Live application link added where applicable
- [ ] Demo video added
- [ ] AI and open-source components documented
- [ ] Setup and usage instructions tested
- [ ] Challenges and learnings documented
- [ ] Devpost submission completed
- [ ] Devpost link added
- [ ] Credits added
- [ ] License added
- [ ] Repository is organized and complete
