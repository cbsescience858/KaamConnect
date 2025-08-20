async function updateDistrictDropdown(stateSelectId, districtSelectId) {
  const stateSelect = document.getElementById(stateSelectId);
  const districtSelect = document.getElementById(districtSelectId);
  if (!stateSelect || !districtSelect) return;
  districtSelect.innerHTML = '<option value="">Loading districts...</option>';
  districtSelect.disabled = true;

  const state = (stateSelect.value || '').trim();
  if (!state) {
    districtSelect.innerHTML = '<option value="">Select District</option>';
    return;
  }

  try {
    const res = await fetch(`/location/districts?state=${encodeURIComponent(state)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const districts = Array.isArray(data.districts) ? data.districts : [];

    districtSelect.innerHTML = '<option value="">Select District</option>';
    if (!districts.length) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'No districts available';
      districtSelect.appendChild(opt);
      return;
    }
    districts.forEach(district => {
      const name = String(district);
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      districtSelect.appendChild(opt);
    });
    districtSelect.disabled = false;
  } catch (e) {
    console.error('Failed to load districts:', e);
    districtSelect.innerHTML = '<option value="">Failed to load districts</option>';
  }
}

// Optional: bind automatically when DOM is ready if elements exist
document.addEventListener('DOMContentLoaded', () => {
  const stateEl = document.getElementById('state');
  const districtEl = document.getElementById('district');
  if (stateEl && districtEl) {
    stateEl.addEventListener('change', () => updateDistrictDropdown('state', 'district'));
    // If a state is pre-selected (e.g., browser back/forward cache), populate immediately
    if (stateEl.value) {
      updateDistrictDropdown('state', 'district');
    }
  }
});
