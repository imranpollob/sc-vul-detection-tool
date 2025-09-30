## Overall Architecture

```mermaid
flowchart TD
  classDef mod fill:#eef,stroke:#88a,stroke-width:1px,color:#111;
  classDef step fill:#fff,stroke:#999,stroke-width:1px,color:#111;
  classDef decision fill:#fff,stroke:#f39c12,stroke-width:2px,color:#111;
  classDef io fill:#f9f9f9,stroke:#bbb,stroke-dasharray:3 3,color:#111;

  S([Start]):::step --> SRC[Solidity Source Code]:::io
  SRC --> M1["Module 1  Program Representation"]:::mod
  M1 --> M2["Module 2  Learning and Detection"]:::mod
  M2 --> D1{Vulnerability Detected?}:::decision
  D1 -- No --> END_NO([End  No Finding]):::step
  D1 -- Yes --> M3["Module 3  Exploit Verification"]:::mod
  M3 --> VVER[Verified Evidence]:::io
  VVER --> M4["Module 4  Analysis and Reporting"]:::mod
  M4 --> REPORT[Security Report and PoC]:::io --> END_YES([End  Verified Finding]):::step
 ```


 ## Module 1 — Foundational Program Representation

 ```mermaid
 flowchart TD
  classDef mod fill:#eef,stroke:#88a,stroke-width:1px,color:#111;
  classDef step fill:#fff,stroke:#999,stroke-width:1px,color:#111;
  classDef io fill:#f9f9f9,stroke:#bbb,stroke-dasharray:3 3,color:#111;

  SRC[Solidity Source Code]:::io --> AST[AST Generation]:::step
  AST --> SYM[Symbol Table and Types]:::step
  ANCH[Anchor Vocabulary  literature and audits]:::io --> MATCH[Anchor Matching]:::step
  AST --> MATCH
  MATCH --> SLICE[Semantic Slicing  control and data deps]:::step
  SLICE --> HPG[HPG Construction  AST CFG DFG inter contract edges]:::step
  HPG --> HPG_OUT((Rich HPG Slices)):::io

  %% notes
  subgraph Notes[" "]
    direction TB
    N1[Anchor sources include CWE patterns and audit corpus]:::io
    N2[Slice depth controlled by config and heuristics]:::io
  end
```

## Module 2 — Core Learning and Detection

```mermaid
flowchart TD
  classDef mod fill:#eef,stroke:#88a,stroke-width:1px,color:#111;
  classDef step fill:#fff,stroke:#999,stroke-width:1px,color:#111;
  classDef io fill:#f9f9f9,stroke:#bbb,stroke-dasharray:3 3,color:#111;

  HPG_OUT((HPG Slices)):::io --> ENC[Shared Hetero GNN Encoder]:::step
  TRAIN_DATA[Training Data  Forge Top200 labels]:::io --> ENC

  ENC --> DET[Detection Head  graph level]:::step
  ENC --> LOC[Localization Head  node level]:::step
  ENC --> PGEN[Proof Generation Head  PoC scaffold generator]:::step

  DET --> SCORE[Detection Scores and Classes]:::io
  LOC --> HIGHLIGHT[Line level localization and subgraph highlight]:::io
  PGEN --> POC[Generated PoC or Test Scaffold]:::io

  %% auxiliary
  LOSS[Multi task loss  detection localization generator]:::step
  ENC --> LOSS
  DET --> LOSS
  LOC --> LOSS
  PGEN --> LOSS
```

## Module 3 — Automated Exploit Verification

```mermaid
flowchart TD
  classDef mod fill:#eef,stroke:#88a,stroke-width:1px,color:#111;
  classDef step fill:#fff,stroke:#999,stroke-width:1px,color:#111;
  classDef decision fill:#fff,stroke:#f39c12,stroke-width:2px,color:#111;
  classDef io fill:#f9f9f9,stroke:#bbb,stroke-dasharray:3 3,color:#111;

  POC[Generated PoC or Test Scaffold]:::io --> SB[Sandbox Setup  ephemeral container and pinned toolchain]:::step
  SB --> ASSEMBLE[Assemble Foundry Project  add target and PoC files]:::step
  ASSEMBLE --> RUN[Run forge test  with gas and time limits]:::step
  RUN --> PARSE[Parse Test Results and Logs]:::step

  PARSE --> DEC{Exploit Verified?}:::decision
  DEC -- Yes --> VERIFIED[Verified Exploit Evidence]:::io
  DEC -- No --> ERR_LOG[Capture errors and logs]:::step --> REFINE[Refine PoC inputs and prompts]:::step --> PGEN[Return to Proof Generator]:::io

  %% optional symbolic execution
  PARSE --> SE[Optional  Symbolic Execution guidance]:::step
  SE --> SE_RES[Path feasibility and reachability]:::step
  SE_RES --> DEC
```

## Module 4 — Analysis and Reporting

```mermaid
flowchart TD
  classDef mod fill:#eef,stroke:#88a,stroke-width:1px,color:#111;
  classDef step fill:#fff,stroke:#999,stroke-width:1px,color:#111;
  classDef io fill:#f9f9f9,stroke:#bbb,stroke-dasharray:3 3,color:#111;

  VERIFIED[Verified Exploit Evidence]:::io --> AGG[Aggregate Findings  detection localization verification]:::step
  AGG --> EXPL[Explainability  highlight subgraph and rationale]:::step
  AGG --> CWE[Map to CWE and severity]:::step
  EXPL --> REP[Generate Developer Report  root cause impact reproduction steps PoC]:::step
  CWE --> REP
  REP --> OUTPUT[Security Report  deliverable with PoC and remediation guidance]:::io

  %% optional outputs
  REP --> DASH[Dashboard update and metrics logging]:::io
  REP --> NOTIFY[Responsible disclosure workflow]:::io
```