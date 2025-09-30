# Installation Guide

Follow the steps below to set up the environment and run the Heterogeneous Program Graph builder for Solidity projects.

## 1. Prerequisites

- **Python**: Version 3.10 or newer.
- **pip**: Updated to the latest release (`python -m pip install --upgrade pip`).
- **Solidity compiler (solc)**: Required by Slither. Install via your package manager or [Solidity releases](https://docs.soliditylang.org/en/latest/installing-solidity.html).
- **Rust toolchain (optional)**: Only needed if Slither pulls packages that require Rust for compilation.

## 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install Python Dependencies

Install the project's requirements:

```bash
pip install -r requirements.txt
```

> **Note:** PyTorch offers GPU- and CPU-specific wheels. If you need a CUDA-enabled build, follow the [official PyTorch installation instructions](https://pytorch.org/get-started/locally/) and install torch before running the `pip install -r requirements.txt` command.

## 4. Verify Slither Setup

Slither front-loads its solc detection. Confirm it runs without errors:

```bash
slither --help
```

If the command fails, ensure `solc` is on your `PATH` and matches one of the versions supported by your contracts.

## 5. Build an HPG

From the repository root, run the script with the path to a Solidity project:

```bash
python build_hpg.py path/to/solidity/project
```

Example using the bundled dummy data:

```bash
python build_hpg.py dummy_dataset/project_single
python build_hpg.py dummy_dataset/project_multi
```

Each run produces a `project_hpg.pt` file in the current working directory containing the serialized `torch_geometric.data.HeteroData` graph.
The script now writes results to the `outputs/` directory, naming each file after the project path (e.g., `outputs/dummy_dataset_project_single.pt`).

## 6. Deactivate the Environment (Optional)

```bash
deactivate
```

That's it—your environment is ready to generate heterogeneous program graphs from Solidity projects.
