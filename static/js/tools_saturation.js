// Saturation and P-h properties are calculated by the same CoolProp endpoint.
    // State Variables
    let currentGaugeType = 'NOT_GAUGE'; // 'NOT_GAUGE' or 'ADD_GAUGE'
    let currentOperatingMode = 'COOLING'; // 'COOLING' or 'HEATING'

    const coilConfigs = {
      cooling: [
        { id: 'c_icc', label: 'c_icc_container', defaultVal: ['10.4', '-0.1', '', '', '', '', '', '', '', ''] },
        { id: 'c_occ', label: 'c_occ_container', defaultVal: ['25.3', '20.8', '', '', '', '', '', '', '', ''] },
        { id: 'c_oco', label: 'c_oco_container', defaultVal: ['25.1', '', '', '', '', '', '', '', '', ''] }
      ],
      heating: [
        { id: 'h_occ', label: 'h_occ_container', defaultVal: ['19.5', '', '', '', '', '', '', '', '', ''] },
        { id: 'h_icc', label: 'h_icc_container', defaultVal: ['48.0', '48.7', '', '', '', '', '', '', '', ''] },
        { id: 'h_ico', label: 'h_ico_container', defaultVal: ['49.7', '48.7', '', '', '', '', '', '', '', ''] }
      ]
    };

    function initCoilGrids() {
      ['cooling', 'heating'].forEach(m => {
        coilConfigs[m].forEach(cfg => {
          const container = document.getElementById(cfg.label);
          if (!container) return;
          container.innerHTML = '';

          // 10 input cells
          for (let i = 0; i < 10; i++) {
            const input = document.createElement('input');
            input.type = 'number';
            input.step = '0.1';
            input.id = `${cfg.id}_${i}`;
            input.value = cfg.defaultVal[i] || '';
            input.className = 'coil-input rounded p-1 font-mono-data';
            input.addEventListener('input', computeCalculations);
            container.appendChild(input);
          }

          // 11th cell: Dedicated Ave Box (Rounded to 1 decimal place)
          const aveBox = document.createElement('div');
          aveBox.id = `${cfg.id}_ave`;
          aveBox.className = 'coil-ave-box font-mono-data';
          aveBox.textContent = '-';
          container.appendChild(aveBox);
        });
      });
    }

    function getRowAverage(rowPrefix) {
      let sum = 0;
      let count = 0;
      for (let i = 0; i < 10; i++) {
        const el = document.getElementById(`${rowPrefix}_${i}`);
        if (el && el.value.trim() !== '') {
          const val = parseFloat(el.value);
          if (!isNaN(val)) {
            sum += val;
            count++;
          }
        }
      }
      const aveBox = document.getElementById(`${rowPrefix}_ave`);
      if (count === 0) {
        if (aveBox) aveBox.textContent = '-';
        return 0;
      }
      // Rounded strictly to 1 decimal place
      const ave = Math.round((sum / count) * 10) / 10;
      if (aveBox) aveBox.textContent = ave.toFixed(1);
      return ave;
    }

    function setRowValues(rowPrefix, values) {
      for (let i = 0; i < 10; i++) {
        const el = document.getElementById(`${rowPrefix}_${i}`);
        if (el) el.value = values[i] !== undefined ? values[i] : '';
      }
      getRowAverage(rowPrefix);
    }

    function getRefrigerant() {
      return document.getElementById('refrigerantSelect').value || 'R32';
    }

    function toggleOperatingMode() {
      if (currentOperatingMode === 'COOLING') {
        setOperatingMode('HEATING');
      } else {
        setOperatingMode('COOLING');
      }
    }

    function setOperatingMode(mode) {
      currentOperatingMode = mode;
      const btn = document.getElementById('operatingModeBtn');
      const coolContainer = document.getElementById('coolingViewContainer');
      const heatContainer = document.getElementById('heatingViewContainer');

      if (mode === 'COOLING') {
        btn.textContent = 'COOLING';
        btn.className = 'px-4 py-1 font-black text-xs sm:text-sm rounded border-2 border-slate-800 shadow-sm transition-all duration-150 uppercase bg-blue-100 text-blue-700 hover:bg-blue-200';
        coolContainer.classList.remove('hidden');
        coolContainer.classList.add('grid');
        heatContainer.classList.add('hidden');
        heatContainer.classList.remove('grid');
      } else {
        btn.textContent = 'HEATING';
        btn.className = 'px-4 py-1 font-black text-xs sm:text-sm rounded border-2 border-slate-800 shadow-sm transition-all duration-150 uppercase bg-red-100 text-red-600 hover:bg-red-200';
        heatContainer.classList.remove('hidden');
        heatContainer.classList.add('grid');
        coolContainer.classList.add('hidden');
        coolContainer.classList.remove('grid');
      }

      computeCalculations();
    }

    function switchGaugeType(type) {
      currentGaugeType = type;
      const btnNot = document.getElementById('tabNotGauge');
      const btnAdd = document.getElementById('tabAddGauge');
      const notSec = document.getElementById('notGaugeTopSection');
      const addSec = document.getElementById('addGaugeTopSection');

      const cRowICC = document.getElementById('c_row_indoor_center');
      const cRowOCC = document.getElementById('c_row_outdoor_center');
      const hRowOCC = document.getElementById('h_row_outdoor_center');
      const hRowICC = document.getElementById('h_row_indoor_center');

      const cFormulaSC = document.getElementById('c_formula_sc').querySelector('span:last-child');
      const cFormulaSH = document.getElementById('c_formula_sh').querySelector('span:last-child');
      const cFormulaDSH = document.getElementById('c_formula_dsh').querySelector('span:last-child');

      const hFormulaSC = document.getElementById('h_formula_sc').querySelector('span:last-child');
      const hFormulaSH = document.getElementById('h_formula_sh').querySelector('span:last-child');
      const hFormulaDSH = document.getElementById('h_formula_dsh').querySelector('span:last-child');

      if (type === 'NOT_GAUGE') {
        btnNot.className = 'sat-mode-tab is-active';
        btnAdd.className = 'sat-mode-tab';
        notSec.classList.remove('hidden');
        notSec.classList.add('flex');
        addSec.classList.add('hidden');
        addSec.classList.remove('grid');

        cRowICC.style.display = 'block';
        cRowOCC.style.display = 'block';
        hRowOCC.style.display = 'block';
        hRowICC.style.display = 'block';

        cFormulaSC.textContent = "OUTDOOR COIL CENTER(AVE) - OUTDOOR COIL OUTLET(AVE)";
        cFormulaSH.textContent = "SUCTION - INDOOR COIL CENTER (AVE)";
        cFormulaDSH.textContent = "DISCHARGE - OUTDOOR COIL CENTER(AVE)";

        hFormulaSC.textContent = "INDOOR COIL CENTER(AVE) - INDOOR COIL OUTLET(AVE)";
        hFormulaSH.textContent = "SUCTION - OUTDOOR COIL CENTER (AVE)";
        hFormulaDSH.textContent = "DISCHARGE - INDOOR COIL CENTER(AVE)";
      } else {
        btnAdd.className = 'sat-mode-tab is-active';
        btnNot.className = 'sat-mode-tab';
        notSec.classList.add('hidden');
        notSec.classList.remove('flex');
        addSec.classList.remove('hidden');
        addSec.classList.add('grid');

        cRowICC.style.display = 'none';
        cRowOCC.style.display = 'none';
        hRowOCC.style.display = 'none';
        hRowICC.style.display = 'none';

        cFormulaSC.textContent = "HIGH SATURATION (BUBBLE) - OUTDOOR COIL OUTLET(AVG)";
        cFormulaSH.textContent = "SUCTION - LOW SATURATION (DEW)";
        cFormulaDSH.textContent = "DISCHARGE - HIGH SATURATION (DEW)";

        hFormulaSC.textContent = "HIGH SATURATION (BUBBLE) - INDOOR COIL OUTLET(AVG)";
        hFormulaSH.textContent = "SUCTION - LOW SATURATION (DEW)";
        hFormulaDSH.textContent = "DISCHARGE - HIGH SATURATION (DEW)";

        calculateAddGaugePT();
      }

      computeCalculations();
    }

    function onRefrigerantChange() {
      const ref = getRefrigerant();
      document.getElementById('bigRefrigBadge').textContent = ref;
      if (currentGaugeType === 'ADD_GAUGE') {
        calculateAddGaugePT();
      }
      computeCalculations();
    }

    // Add Gauge: Pressure inputs -> Saturation Temp using SatTemp function
    function calculateAddGaugePT() { computeCalculations(); }

    function computeCalculations() {
      const averages = {};
      ['c_icc','c_occ','c_oco','h_occ','h_icc','h_ico'].forEach(id => {
        averages[id] = getRowAverage(id);
      });
      const cooling = currentOperatingMode === 'COOLING';
      const prefix = cooling ? 'c' : 'h';
      const payload = {
        refrigerant: getRefrigerant(), gauge: currentGaugeType,
        high_pressure: document.getElementById('agHiPress').value,
        low_pressure: document.getElementById('agLowPress').value,
        high_temperature: averages[cooling ? 'c_occ' : 'h_icc'],
        low_temperature: averages[cooling ? 'c_icc' : 'h_occ'],
        suction: document.getElementById(prefix + '_suction').value,
        discharge: document.getElementById(prefix + '_discharge').value,
        liquid: averages[cooling ? 'c_oco' : 'h_ico']
      };
      const needed = currentGaugeType === 'NOT_GAUGE'
        ? (cooling ? ['c_icc','c_occ','c_oco'] : ['h_occ','h_icc','h_ico'])
        : [cooling ? 'c_oco' : 'h_ico'];
      const missing = needed.some(id => document.getElementById(id + '_ave').textContent === '-');
      window.updatePHDiagram(payload, cooling ? 'cooling' : 'heating', missing);
    }

    function loadSamplePreset(presetNum) {
      if (presetNum === 3) {
        document.getElementById('refrigerantSelect').value = 'R32';
        document.getElementById('bigRefrigBadge').textContent = 'R32';
        switchGaugeType('ADD_GAUGE');
        document.getElementById('agHiPress').value = '2.5';
        document.getElementById('agLowPress').value = '0.9';
        ['c','h'].forEach(prefix => {
          document.getElementById(prefix + '_suction').value = '15';
          document.getElementById(prefix + '_discharge').value = '80';
        });
        setRowValues('c_oco', ['35']);
        setRowValues('h_ico', ['35']);
        setOperatingMode('COOLING');
      } else if (presetNum === 1) {
        // Image 1 & 2: Not Gauge Mode
        document.getElementById('refrigerantSelect').value = 'R32';
        document.getElementById('bigRefrigBadge').textContent = 'R32';
        switchGaugeType('NOT_GAUGE');

        // Cooling panel values
        document.getElementById('c_suction').value = '11.5';
        document.getElementById('c_discharge').value = '38.6';
        setRowValues('c_icc', ['10.4', '-0.1', '', '', '', '', '', '', '', '']);
        setRowValues('c_occ', ['25.3', '20.8', '', '', '', '', '', '', '', '']);
        setRowValues('c_oco', ['25.1', '', '', '', '', '', '', '', '', '']);

        // Heating panel values
        document.getElementById('h_suction').value = '19.3';
        document.getElementById('h_discharge').value = '58.7';
        setRowValues('h_occ', ['19.5', '', '', '', '', '', '', '', '', '']);
        setRowValues('h_icc', ['48.0', '48.7', '', '', '', '', '', '', '', '']);
        setRowValues('h_ico', ['49.7', '48.7', '', '', '', '', '', '', '', '']);

        setOperatingMode('COOLING');

      } else if (presetNum === 2) {
        // Image 3 & 4: Add Gauge Mode
        document.getElementById('refrigerantSelect').value = 'R32';
        document.getElementById('bigRefrigBadge').textContent = 'R32';
        switchGaugeType('ADD_GAUGE');

        document.getElementById('agHiPress').value = '2.511';
        document.getElementById('agLowPress').value = '1.283';
        calculateAddGaugePT();

        // Cooling panel values
        document.getElementById('c_suction').value = '18.8';
        document.getElementById('c_discharge').value = '59.8';
        setRowValues('c_oco', ['39.4', '', '', '', '', '', '', '', '', '']);

        // Heating panel values
        document.getElementById('h_suction').value = '-6.6';
        document.getElementById('h_discharge').value = '56.1';
        setRowValues('h_ico', ['25.4', '24.6', '', '', '', '', '', '', '', '']);

        setOperatingMode('COOLING');
      }

      computeCalculations();
    }

    function copyLiveValues(source, clone) {
      const sourceFields = source.querySelectorAll('input, select, textarea');
      const cloneFields = clone.querySelectorAll('input, select, textarea');
      sourceFields.forEach((field, index) => {
        if (!cloneFields[index]) return;
        cloneFields[index].value = field.value;
        cloneFields[index].setAttribute('value', field.value);
      });
      clone.querySelectorAll('[id]').forEach(element => element.removeAttribute('id'));
    }

    function fitSaturationPreview() {
      const page = document.getElementById('exportPreviewPage');
      const report = page.querySelector('.sat-export-preview-report');
      if (!report) return;
      report.style.transform = 'none';
      report.style.left = '0px';
      report.style.top = '0px';
      const availableWidth = page.clientWidth - 28;
      const availableHeight = page.clientHeight - 28;
      const scale = Math.min(availableWidth / report.scrollWidth, availableHeight / report.scrollHeight, 1);
      report.style.transform = `scale(${scale})`;
      const scaledWidth = report.scrollWidth * scale;
      const scaledHeight = report.scrollHeight * scale;
      report.style.left = `${Math.max(14, (page.clientWidth - scaledWidth) / 2)}px`;
      report.style.top = `${Math.max(14, (page.clientHeight - scaledHeight) / 2)}px`;
    }

    function clearSaturationValues() {
      document.querySelectorAll('.coil-input, #agHiPress, #agLowPress, #c_suction, #c_discharge, #h_suction, #h_discharge').forEach(input => {
        input.value = '';
      });
      ['c_icc','c_occ','c_oco','h_occ','h_icc','h_ico'].forEach(getRowAverage);
      if (window.resetPHDiagrams) {
        window.resetPHDiagrams('Values cleared. Enter new data to calculate again.');
      }
    }

    function exportSaturationReport() {
      const modal = document.getElementById('exportPreviewModal');
      const page = document.getElementById('exportPreviewPage');
      const report = document.createElement('div');
      const headerSource = document.querySelector('.excel-header');
      const modeSource = document.getElementById(currentOperatingMode === 'HEATING' ? 'heatingViewContainer' : 'coolingViewContainer');
      const headerClone = headerSource.cloneNode(true);
      const modeClone = modeSource.cloneNode(true);

      copyLiveValues(headerSource, headerClone);
      copyLiveValues(modeSource, modeClone);
      modeClone.classList.remove('hidden');
      modeClone.classList.add('grid', 'sat-export-preview-mode');
      report.className = 'sat-export-preview-report';
      report.append(headerClone, modeClone);
      page.replaceChildren(report);
      modal.hidden = false;
      document.body.classList.add('export-preview-open');
      requestAnimationFrame(fitSaturationPreview);
    }

    function closeSaturationExportPreview() {
      document.getElementById('exportPreviewModal').hidden = true;
      document.body.classList.remove('export-preview-open');
    }

    function confirmSaturationExport() {
      closeSaturationExportPreview();
      const originalTitle = document.title;
      const ref = getRefrigerant();
      const mode = currentOperatingMode === 'HEATING' ? 'Heating' : 'Cooling';
      const today = new Date();
      const date = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, '0'), String(today.getDate()).padStart(2, '0')].join('-');
      let restored = false;
      const restore = () => {
        if (restored) return;
        restored = true;
        document.body.classList.remove('print-report');
        document.title = originalTitle;
      };

      document.title = `Saturation_Temp_${ref}_${mode}_${date}`;
      document.body.classList.add('print-report');
      window.addEventListener('afterprint', restore, { once: true });
      requestAnimationFrame(() => {
        window.print();
        window.setTimeout(restore, 1500);
      });
    }

    // Initialization on load
    window.addEventListener('DOMContentLoaded', () => {
      initCoilGrids();
      loadSamplePreset(3);
    });
    window.addEventListener('resize', () => {
      if (!document.getElementById('exportPreviewModal').hidden) fitSaturationPreview();
    });
    window.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !document.getElementById('exportPreviewModal').hidden) closeSaturationExportPreview();
    });
  
