![OS](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-blue?style=flat-square)
[![Python](https://img.shields.io/badge/Python-%20%203.8%20|%203.9%20|%203.10%20|%203.11-blue?logo=python&style=flat-square)](https://github.com/cda-tum/mnt-opdom-explorer/actions)
[![CI](https://img.shields.io/github/actions/workflow/status/cda-tum/mnt-opdom-explorer/ci.yml?style=flat-square&logo=github&label=CI)](https://github.com/cda-tum/mnt-opdom-explorer/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/cda-tum/mnt-opdom-explorer?label=Coverage&logo=codecov&style=flat-square)](https://codecov.io/gh/cda-tum/mnt-opdom-explorer)
[![License](https://img.shields.io/github/license/cda-tum/mnt-opdom-explorer?label=License&style=flat-square)](https://github.com/cda-tum/mnt-opdom-explorer/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/cda-tum/mnt-opdom-explorer?label=Release&style=flat-square)](https://github.com/cda-tum/mnt-opdom-explorer/releases)
[![IEEEXplore](https://img.shields.io/static/v1?label=ACM&message=Paper&color=informational&style=flat-square)](https://dl.acm.org/doi/10.1145/3611315.3633246)

# **Operational Domain Explorer**

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/cda-tum/fiction/main/docs/_static/mnt_light.svg" width="60%">
    <img src="https://raw.githubusercontent.com/cda-tum/fiction/main/docs/_static/mnt_dark.svg" width="60%">
  </picture>
</p>

The _Operational Domain Explorer_ is a PyQt6 application that enables insight into the robustness of
_Silicon Dangling Bond_ (SiDB) gates against material imperfections at the atomic scale. To this end, it relies on
physical simulation tools implemented in the [_fiction_ framework](https://github.com/cda-tum/fiction). The Operational
Domain Explorer is developed as part of the _Munich Nanotech Toolkit_ (_MNT_) by
the [Chair for Design Automation](https://www.cda.cit.tum.de/) at
the [Technical University of Munich](https://www.tum.de/).

## Operational Domain Analysis

The *Operational Domain* was proposed as a methodology to evaluate the extent of physical parameter variations that an
SiDB logic gate can tolerate by plotting the logical correctness of that gate's behavior across a predetermined range of
physical parameters. Given an SiDB layout *L* and a Boolean function *f : 𝔹ⁿ ⟶ 𝔹ᵐ*, the operational domain of *L* given
*f* is defined in the parameter space as the set of coordinate points for which *L* implements *f*. To determine whether
*L* implements *f* at any given coordinate point *(x, y, z)*, this point can be sampled, i.e., by conducting *2ⁿ*
physical simulations—one for each possible input pattern of *L*.

## Getting Started

---

### Prerequisites

Before you get started, make sure you have the following installed:

- **Python 3.9 or newer**: This project requires Python 3.8+ to run.
- **Git**: To clone the repository.

### Step 1: Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/cda-tum/opdom-explore.git
cd opdom-explore
```

### Step 2: Set Up a Virtual Environment (Recommended)

It's a good practice to use a virtual environment to manage dependencies. You can set up a virtual environment by
running:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
```

Using `uv` as a package manager? Set up the virtual environment with:

   ```bash
   uv venv 
   source .venv/bin/activate
   ```

### Step 3: Install Dependencies

With the virtual environment active:

   ```bash
   pip install --upgrade pip
   pip install .
   ```

For `uv`, use:

   ```bash
   uv run
   ```

### Step 4: Running the Application

To start the Operational Domain Explorer, you can run the application as follows:

```bash
python -m main 
```

### Step 5: Running Tests

To verify functionality:

```bash
pytest test
```

[`nox`](https://nox.thea.codes/en/stable/index.html) can be used to conveniently run many development tasks like
testing the bindings on multiple Python installations.
Here’s the command split into individual steps for clarity:

1. Install `nox` using the `uv` tool:  
   ```bash
   uv tool install nox
   ```

2. Run the tests using `nox`:  
   ```bash
   nox -s tests
   ```

### Step 6: Contributing

If you're interested in contributing, feel free to fork the repository and submit pull requests. Make sure to follow the
coding guidelines and run tests before submitting your PR.

For more details, check the [repository](https://github.com/cda-tum/opdom-explore).

## Reference

If you use the *Operational Domain Explorer* for academic purposes, we would be thankful if you referred to it by citing
the following publication:

```bibtex
@inproceedings{walter2023opdom,
    title = {{Reducing the Complexity of Operational Domain Computation in Silicon Dangling Bond Logic}},
    author = {Walter, Marcel and Drewniok, Jan and Ng, Samuel Sze Hang and Walus, Konrad and Wille, Robert},
    booktitle = {International Symposium on Nanoscale Architectures (NANOARCH)},
}
```

---

## License

This project is licensed under the [Prosperity Public License 3.0.0](https://prosperitylicense.com/versions/3.0.0).

- **Permitted Use:** You are free to use this software for personal, academic, and other non-commercial purposes.
- **Prohibited Use:** Commercial use of this software is not permitted under this license. Any form of direct or
  indirect commercial exploitation is strictly prohibited without obtaining a commercial license first.

If you would like to obtain a commercial license to use this project in a business, product, or any profit-driven
environment, please reach out directly for licensing terms.

For further details, please refer to
the [LICENSE.md](https://github.com/cda-tum/mnt-opdom-explorer/blob/main/LICENSE.md) file in this repository.

---

## Acknowledgements

The Munich Nanotech Toolkit has been supported by the Bavarian State Ministry for Science and Arts through the
Distinguished Professorship Program.

<p align="center">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/cda-tum/mqt/main/docs/_static/tum_dark.svg" width="28%">
        <img src="https://raw.githubusercontent.com/cda-tum/mqt/main/docs/_static/tum_light.svg" width="28%" alt="TUM Logo">
    </picture>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <!-- Non-breaking spaces for spacing -->
    <picture>
        <img src="https://raw.githubusercontent.com/cda-tum/mqt/main/docs/_static/logo-bavaria.svg" width="16%" alt="Coat of Arms of Bavaria">
    </picture>
</p>
