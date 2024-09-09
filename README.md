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