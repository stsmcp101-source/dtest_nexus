# Saturation temperature and P-h calculations

The original attached HTML used a fixed SVG and an unvalidated pressure/temperature polynomial. The calculator now uses CoolProp HEOS for both its numerical results and its diagram so they share one property model.

- P-h horizontal axis: specific enthalpy, kJ/kg. Vertical axis: absolute pressure in MPa on a logarithmic scale.
- User pressure inputs: gauge pressure MPa(g). Add 0.101325 MPa (standard atmosphere) before property evaluation. This is a fixed atmospheric reference, not local altitude compensation.
- R32, R410A, propane (R290), and the predefined R454B mixture use CoolProp's fluid definitions.
- SC uses condenser bubble temperature; SH uses evaporator dew temperature; DSH uses condenser dew temperature. Coil-center measurements in Not Gauge mode are approximations to these saturation temperatures.
- 1: compressor inlet (low pressure, measured suction temperature).
- 2: compressor outlet (high pressure, measured discharge temperature).
- 3: condenser outlet (high pressure, average measured liquid outlet temperature).
- 4: expansion outlet, same enthalpy as point 3 and evaporator pressure.
- 1–2 is a dashed connector between measured endpoints, not a calculated compression trajectory or an isentropic line. Pressure losses and heat losses in connecting pipes are not modeled.
- Invalid phase assumptions (negative SC, SH, DSH), unsupported saturation states, or inconsistent enthalpy ordering do not produce a misleading closed refrigeration cycle. The UI shows an explanation instead.
- The diagram is an engineering model based on the entered measurements; it is not a measurement of the full process path.

References:
- https://coolprop.org/coolprop/HighLevelAPI.html
- https://coolprop.org/fluid_properties/Mixtures.html
- https://assets.danfoss.com/documents/latest/35513/AN227186438976en-000301.pdf
