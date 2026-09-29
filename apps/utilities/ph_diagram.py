"""Refrigerant property calculations in SI; P-h output uses MPa(abs), kJ/kg.

References: https://coolprop.org/coolprop/HighLevelAPI.html
https://assets.danfoss.com/documents/latest/35513/AN227186438976en-000301.pdf
No pressure losses assumed; expansion is isenthalpic. Compression endpoints
are measured states, not an assumed isentropic compressor trajectory.
"""
import math
from functools import lru_cache
import CoolProp as CP
from CoolProp.CoolProp import PropsSI

FLUIDS = {'R32':'R32', 'R410A':'R410A', 'R454B':'R454B.mix', 'R290':'R290'}
ATM = 101325.0


def number(data, key, low, high):
    try:
        value = float(data[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f'Enter a numeric value for {key}.')
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{key} must be between {low} and {high}.')
    return value


@lru_cache(maxsize=4)
def envelope(ref):
    fluid = FLUIDS[ref]
    liquid, vapor = [], []
    if ref == 'R454B':
        # Trace the true mixture phase envelope (including the near-critical
        # turn) rather than forcing the pure-fluid dome construction on it.
        state = CP.AbstractState('HEOS', fluid)
        state.build_phase_envelope('dummy')
        data = state.get_phase_envelope_data()
        mass = state.molar_mass()
        for i, p in enumerate(data.p):
            if p < 50000:
                continue
            point = [data.hmolar_vap[i] / mass / 1000, p / 1e6]
            (vapor if data.Q[i] == 1 else liquid).append(point)
        liquid.reverse()
        # The solver crosses the critical neighborhood continuously between
        # the dew and bubble branches. Include that connecting segment.
        if liquid and vapor:
            vapor.append(liquid[-1])
    else:
        pc = PropsSI('Pcrit', fluid)
        pressures = [50000 * (pc * .995 / 50000) ** (i / 149) for i in range(150)]
        pressures += [pc * fraction for fraction in [.998, .999, .9995, .9999, .99999]]
        for p in pressures:
            try:
                hl = PropsSI('H','P',p,'Q',0,fluid) / 1000
                hv = PropsSI('H','P',p,'Q',1,fluid) / 1000
                liquid.append([hl,p/1e6]); vapor.append([hv,p/1e6])
            except ValueError:
                continue
        if ref in ('R32','R290'):
            hc = PropsSI('H','T',PropsSI('Tcrit',fluid),'Dmolar',PropsSI('rhomolar_critical',fluid),fluid)/1000
            liquid.append([hc,pc/1e6]);vapor.append([hc,pc/1e6])
        else:
            # Pseudo-pure R410A has a narrow bubble/dew offset. Join only
            # the numerically resolved near-critical endpoints.
            vapor.append(liquid[-1])
    if len(liquid) < 10 or len(vapor) < 10:
        raise ValueError('Unable to generate the saturation envelope for this refrigerant.')
    return {'liquid':liquid, 'vapor':vapor}


def calculate(data):
    ref = data.get('refrigerant')
    if ref not in FLUIDS:
        raise ValueError('The selected refrigerant is not supported.')
    fluid = FLUIDS[ref]
    gauge = data.get('gauge')
    if gauge not in ('ADD_GAUGE','NOT_GAUGE'):
        raise ValueError('Select a pressure mode.')
    if gauge == 'ADD_GAUGE':
        ph = number(data,'high_pressure',0,8)*1e6 + ATM
        pl = number(data,'low_pressure',0,8)*1e6 + ATM
    else:
        # Coil-center temperatures approximate the saturation temperatures.
        # Bubble point on condenser side; dew point on evaporator side.
        th = number(data,'high_temperature',-70,90)+273.15
        tl = number(data,'low_temperature',-70,90)+273.15
        ph = PropsSI('P','T',th,'Q',0,fluid)
        pl = PropsSI('P','T',tl,'Q',1,fluid)
    if ph <= pl:
        raise ValueError('High-side pressure must be greater than low-side pressure.')
    th_bubble = PropsSI('T','P',ph,'Q',0,fluid)-273.15
    th_dew = PropsSI('T','P',ph,'Q',1,fluid)-273.15
    tl_dew = PropsSI('T','P',pl,'Q',1,fluid)-273.15
    suction = number(data,'suction',-100,200)
    discharge = number(data,'discharge',-100,250)
    outlet = number(data,'liquid',-100,150)
    sc, sh, dsh = th_bubble-outlet, suction-tl_dew, discharge-th_dew
    result = {'refrigerant':ref, 'envelope':envelope(ref),
              'high_pressure':ph/1e6,'low_pressure':pl/1e6,
              'high_gauge':(ph-ATM)/1e6,'low_gauge':(pl-ATM)/1e6,
              'high_temperature':th_bubble,'high_dew':th_dew,'low_temperature':tl_dew,
              'sc':sc,'sh':sh,'dsh':dsh, 'points':[], 'warnings':[]}
    for value, message in [(sc,'Negative SC: condenser outlet temperature is above the bubble point.'),
                           (sh,'Negative SH: suction temperature is below the dew point.'),
                           (dsh,'Negative DSH: discharge temperature is below the high-side dew point.')]:
        if value < -0.001:
            result['warnings'].append(message)
    def enthalpy(p,t,quality,sat):
        if abs(t-sat) < 0.001:
            return PropsSI('H','P',p,'Q',quality,fluid)/1000
        return PropsSI('H','P',p,'T',t+273.15,fluid)/1000
    h1=enthalpy(pl,suction,1,tl_dew)
    h2=enthalpy(ph,discharge,1,th_dew)
    h3=enthalpy(ph,outlet,0,th_bubble)
    if h2 <= h1 or h1 <= h3:
        result['warnings'].append('The enthalpy values are inconsistent with compression and heat absorption; verify the measured readings.')
    result['points']=[{'n':1,'h':h1,'p':pl/1e6,'t':suction},
                      {'n':2,'h':h2,'p':ph/1e6,'t':discharge},
                      {'n':3,'h':h3,'p':ph/1e6,'t':outlet},
                      {'n':4,'h':h3,'p':pl/1e6,'t':None}]
    result['saturation']={'liquid_high':PropsSI('H','P',ph,'Q',0,fluid)/1000,
                          'vapor_high':PropsSI('H','P',ph,'Q',1,fluid)/1000,
                          'vapor_low':PropsSI('H','P',pl,'Q',1,fluid)/1000}
    return result
