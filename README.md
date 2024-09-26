[![Ubuntu CI](https://img.shields.io/github/actions/workflow/status/cda-tum/mnt-opdom-explorer/ci.yml?label=Ubuntu&logo=ubuntu&style=flat-square)](https://github.com/cda-tum/fiction/actions/workflows/ci.yml)
[![macOS CI](https://img.shields.io/github/actions/workflow/status/cda-tum/mnt-opdom-explorer/ci.yml?label=macOS&logo=apple&style=flat-square)](https://github.com/cda-tum/fiction/actions/workflows/ci.yml)
[![Windows CI](https://img.shields.io/github/actions/workflow/status/cda-tum/mnt-opdom-explorer/ci.yml?label=Windows&logo=windows&style=flat-square)](https://github.com/cda-tum/fiction/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/cda-tum/mnt-opdom-explorer?label=License&style=flat-square)](https://github.com/cda-tum/mnt-opdom-explorer/blob/main/LICENSE)
[![codecov](https://img.shields.io/codecov/c/github/cda-tum/mnt-opdom-explorer?style=flat-square&logo=codecov)](https://codecov.io/gh/cda-tum/mnt-opdom-explorer)
[![Release](https://img.shields.io/github/v/release/cda-tum/mnt-opdom-explorer?label=opdomain-explore&style=flat-square)](https://github.com/cda-tum/mnt-opdom-explorer/releases)
[![IEEEXplore](https://img.shields.io/static/v1?label=ACM&message=OpDomain&color=informational&style=flat-square)](https://dl.acm.org/doi/10.1145/3611315.3633246)

# Operational Domain Explorer

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/cda-tum/fiction/main/docs/_static/mnt_light.svg" width="60%">
    <img src="https://raw.githubusercontent.com/cda-tum/fiction/main/docs/_static/mnt_dark.svg" width="60%">
  </picture>
</p>

The _Operational Domain Explorer_ is a Qt6 application written in Python that enables insight into the robustness of
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

## Reference

Since the *Operational Domain Explorer* is an academic software, we would be thankful if you referred to it by citing the following publications:

```bibtex
@inproceedings{walter2023opdom,
    title={{Reducing the Complexity of Operational Domain Computation in Silicon Dangling Bond Logic}},
    author={Walter, Marcel and Drewniok, Jan and Ng, Samuel Sze Hang and Walus, Konrad and Wille, Robert},
    booktitle={International Symposium on Nanoscale Architectures (NANOARCH)},
}
```


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