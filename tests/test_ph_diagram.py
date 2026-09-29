import math
from django.test import TestCase
from django.urls import reverse
from CoolProp.CoolProp import PropsSI
from apps.utilities.ph_diagram import calculate, FLUIDS


class PHDiagramTests(TestCase):
    def payload(self, ref='R32'):
        fluid=FLUIDS[ref]
        ph,pl=2.6e6,1e6
        return dict(refrigerant=ref,gauge='ADD_GAUGE',high_pressure=(ph-101325)/1e6,
                    low_pressure=(pl-101325)/1e6,
                    suction=PropsSI('T','P',pl,'Q',1,fluid)-273.15+8,
                    discharge=PropsSI('T','P',ph,'Q',1,fluid)-273.15+40,
                    liquid=PropsSI('T','P',ph,'Q',0,fluid)-273.15-5)

    def test_all_refrigerants_physics(self):
        for ref in FLUIDS:
            with self.subTest(ref=ref):
                data=self.payload(ref)
                result=calculate(data)
                self.assertFalse(result['warnings'])
                self.assertEqual(len(result['points']),4)
                self.assertAlmostEqual(result['high_pressure'],2.6)
                self.assertAlmostEqual(result['low_pressure'],1)
                self.assertAlmostEqual(result['sc'],5)
                self.assertAlmostEqual(result['sh'],8)
                self.assertAlmostEqual(result['dsh'],40)
                points=result['points']
                self.assertEqual(points[2]['h'],points[3]['h'])
                self.assertGreater(points[1]['h'],points[0]['h'])
                self.assertGreater(points[0]['h'],points[3]['h'])
                self.assertAlmostEqual(points[0]['h'],PropsSI('H','P',1e6,'T',data['suction']+273.15,FLUIDS[ref])/1000)
                self.assertGreater(len(result['envelope']['liquid']),10)

    def test_invalid_cycle_is_drawn_with_warning(self):
        data=self.payload();data['suction']=-50
        result=calculate(data)
        self.assertTrue(result['warnings'])
        self.assertEqual(len(result['points']),4)

    def test_no_gauge_negative_sc_still_returns_measured_cycle(self):
        data=self.payload()
        data.update(gauge='NOT_GAUGE', high_temperature=23.1,
                    low_temperature=5.2, liquid=35)
        result=calculate(data)
        self.assertLess(result['sc'],0)
        self.assertTrue(result['warnings'])
        self.assertEqual(len(result['points']),4)
        self.assertEqual(result['points'][2]['h'],result['points'][3]['h'])

    def test_missing_nonfinite_and_reversed_pressure_rejected(self):
        for changes in [{'suction':''},{'high_pressure':'nan'},{'high_pressure':0.2},{'refrigerant':'unknown'}]:
            data=self.payload();data.update(changes)
            with self.assertRaises(ValueError):calculate(data)

    def test_no_gauge_temperature_to_pressure(self):
        data=self.payload()
        original=calculate(data)
        data.update(gauge='NOT_GAUGE',high_temperature=original['high_temperature'],low_temperature=original['low_temperature'])
        result=calculate(data)
        self.assertAlmostEqual(result['high_pressure'],original['high_pressure'],places=5)
        self.assertAlmostEqual(result['low_pressure'],original['low_pressure'],places=5)

    def test_endpoint(self):
        response=self.client.get(reverse('utilities:ph_diagram_data'),self.payload())
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['points']),4)
        self.assertEqual(self.client.get(reverse('utilities:ph_diagram_data'),{'refrigerant':'R32'}).status_code,400)
