# flow-theory

`flow-theory` is a Python toolkit for theoretical estimates in high-speed
aerodynamics: flat-plate skin friction and Stanton number, bow-shock standoff
and shape, entropy-layer swallowing distance, and boundary-layer transition.

## Quick Start

### Install

```bash
pip install flow-theory
```

### Run

=== "CLI"

    ```bash
    flow-theory cf --mach 5.0 --re-x 1e7 --tw-te 0.5
    ```

=== "API"

    ```python
    from flow_theory import cf_laminar

    cf = cf_laminar(
        x=1.0,
        re1=1.0e7,
        mach=5.0,
        temp_edge=250.0,
        temp_wall=125.0,
        wall_type="isothermal",
    )
    print(f"cf = {cf:.6e}")
    ```

## Feedback & Contributing

Questions, bug reports, and contributions are welcome. If something unexpected
comes up while using this package, or there are ideas for improvement, opening
an issue or starting a discussion is the best first step.

Using a label when opening an issue helps prioritize and track requests:

- [Ask a question](https://github.com/hypersonic-aero/flow-theory/issues/new?labels=question)
- [Report a bug](https://github.com/hypersonic-aero/flow-theory/issues/new?labels=bug)
- [Suggest a feature](https://github.com/hypersonic-aero/flow-theory/issues/new?labels=enhancement)

## License

GNU General Public License v3.0 or later. See
[LICENSE](https://github.com/hypersonic-aero/flow-theory/blob/main/LICENSE) for the
complete license terms.
