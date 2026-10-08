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

| Approach |	Limitation |	ArchDrift |
| Manual updates and review checklists |	Easy to forget, and nothing enforces them |	Automated check that can fail CI |
| Diagram-as-code tools (Mermaid, PlantUML, Structurizr) | Still need humans to keep the text in sync with the code | Compares the text against the code and flags mismatches |
| Auto-generate diagrams from code	| Produces a new diagram but ignores the curated one, and gives no explanation of what changed |	Starts from the team's own diagram and reports the specific differences |
| Asking an LLM to review the docs |	Unverifiable and inconsistent	| Deterministic graph diff with citations and confidence levels |

In short: ArchDrift treats documentation drift as a detectable, explainable, and fixable bug, using AI only for the part that needs it, which is reading pictures.

## Technical Implementation

### Architecture

## Architecture

```mermaid
flowchart TD
    subgraph Input["Repository Input"]
        A1[Mermaid diagrams<br/>.md / .mmd]
        A2[SVG diagrams]
        A3[PNG diagrams]
        A4[Source code<br/>routes, imports, ASTs]
        A5[Config files<br/>docker-compose, k8s, .env]
    end

    D[Diagram Discovery<br/>scans repo for diagrams]

    subgraph Diagram["Diagram Graph Extraction"]
        P1[Mermaid / SVG Parser<br/>deterministic]
        G4[Gemma 4 multimodal<br/>via Ollama]
        S[Schema validation<br/>Pydantic JSON nodes + edges]
    end

    subgraph Code["Code Graph Extraction"]
        C1[Static analysis<br/>ast + tree-sitter]
        C2[Config parser<br/>PyYAML]
    end

    DG[(Diagram Graph)]
    CG[(Code Graph)]

    M[Component Matcher<br/>names, paths, config]
    DIFF[Graph Diff Engine<br/>NetworkX]

    subgraph Findings["Drift Classification"]
        F1[Missing in diagram]
        F2[Stale in diagram]
        F3[Changed connection]
    end

    R[Drift Report<br/>file:line evidence + confidence]
    GEN[Mermaid Generator<br/>updated diagram]
    V[mermaid-cli<br/>render + validate]

    subgraph Output["Outputs"]
        O1[CLI report<br/>archdrift check]
        O2[GitHub PR comment]
        O3[Updated Mermaid diagram<br/>replaces stale image]
        O4[CI pass / fail]
    end

    A1 --> D
    A2 --> D
    A3 --> D
    D --> P1
    D --> G4
    P1 --> S
    G4 --> S
    S --> DG

    A4 --> C1
    A5 --> C2
    C1 --> CG
    C2 --> CG

    DG --> M
    CG --> M
    M --> DIFF
    DIFF --> F1
    DIFF --> F2
    DIFF --> F3
    F1 --> R
    F2 --> R
    F3 --> R
    R --> GEN
    GEN --> V

    R --> O1
    R --> O2
    R --> O4
    V --> O3

    style G4 fill:#e8dcff,stroke:#7c5cd6,stroke-width:2px
    style DIFF fill:#d8f0e0,stroke:#2e8b57,stroke-width:2px
```

- **Purple (Gemma 4):** the only AI step. It reads image diagrams and outputs structured JSON, which is validated before use.
- **Green (Graph Diff Engine):** the deterministic core that decides what counts as drift, so every finding is explainable.
- **Two parallel extraction paths** (diagram and code) feed one comparison, and the results fan out to the CLI, PR comments, CI status and a regenerated diagram.

### Technology Stack

| Category        | Technologies                |
| --------------- | --------------------------- |
| Frontend        | **N/A** for the core tool (CLI and CI output). Optional: a static HTML drift report      |
| Backend         | Python 3.11+, Typer (CLI), Pydantic (graph and finding schemas), NetworkX (graph diff), Python ast and tree-sitter (code analysis), PyYAML (Docker Compose and Kubernetes parsing)       |
| Database        | **N/A** Graphs and reports are stored as JSON files       |
| AI / ML         | Gemma 4 (open-weight, multimodal) reads PNG/SVG diagrams and extracts nodes and edges as schema-constrained JSON. Served locally through Ollama, so the whole pipeline stays open-source |
| Infrastructure  | GitHub Actions (CI drift check on pull requests), Docker (packaged CLI), pre-commit hook, pytest      |
| APIs / Services | GitHub API (posts drift findings as PR comments), Mermaid CLI (mermaid-cli) to render and validate generated diagrams, agent skill interface           |


### How It Works

[Explain the major components of the system and how they interact.]

### Technical Decisions

[Explain important architectural, algorithmic, or engineering decisions made during development.]

## Implementation During the Hackathon

[Describe what the team built during the Hack Day and the major functionality or components completed during the event.]

### Team Contributions

- **Raghunathan B K:** [Contribution]
- **Kaevin P:** [Contribution]
- **Viswanath A G:** [Contribution]
- **Sanjay Siddhakumar:** [Contribution]

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
