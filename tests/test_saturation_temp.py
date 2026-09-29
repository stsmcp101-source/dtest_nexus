from django.test import TestCase
from django.urls import reverse
from apps.utilities.forms import ToolIconSettingsForm


class SaturationTempTests(TestCase):
    def test_engineering_card_and_public_calculator(self):
        url = reverse('utilities:engineering_tool', args=['saturation-temp'])
        self.assertContains(self.client.get(reverse('utilities:index')), url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for item in ['refrigerantSelect', 'R32', 'R410A', 'R454B', 'R290',
                     'svgCooling', 'svgHeating', 'tabNotGauge', 'tabAddGauge',
                     'tools_saturation.js', 'saturation_temp_utilities.css']:
            self.assertContains(response, item)
        self.assertNotContains(response, 'cdn.tailwindcss.com')
        self.assertIn('icon_saturation_temp', ToolIconSettingsForm().fields)

    def test_wrong_group_is_not_found(self):
        self.assertEqual(self.client.get(reverse('utilities:calculators_tool', args=['saturation-temp'])).status_code, 404)
