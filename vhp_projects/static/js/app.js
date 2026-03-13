/* VHP Patient Database - Client-side JavaScript */

/**
 * Toggle the daily log print form visibility.
 */
function toggleDailyLogForm() {
    const form = document.getElementById('dailyLogForm');
    if (form.style.display === 'none' || form.style.display === '') {
        form.style.display = 'block';
    } else {
        form.style.display = 'none';
    }
}

/**
 * Confirm deletion of a patient before submitting the form.
 */
function confirmDelete(form, patientName) {
    if (confirm(`Are you sure you want to delete patient "${patientName}"? This action cannot be undone.`)) {
        form.submit();
    }
}

/**
 * Toggle a print dropdown menu using a portal approach.
 * The menu is cloned and appended to <body> with fixed positioning
 * to avoid overflow/clipping issues inside the table.
 */
var activePortal = null;

function closePortal() {
    if (activePortal) {
        activePortal.remove();
        activePortal = null;
    }
}

function togglePrintMenu(patientId) {
    var menu = document.getElementById('printMenu' + patientId);
    var button = menu.previousElementSibling;

    // If portal is already open for this menu, close it
    if (activePortal && activePortal.dataset.forPatient === String(patientId)) {
        closePortal();
        return;
    }

    // Close any existing portal
    closePortal();

    // Create portal: clone the dropdown content and append to body
    var portal = document.createElement('div');
    portal.className = 'dropdown-portal';
    portal.dataset.forPatient = String(patientId);

    // Copy the dropdown items into the portal
    var items = menu.querySelectorAll('.dropdown-item');
    for (var i = 0; i < items.length; i++) {
        var link = items[i].cloneNode(true);
        portal.appendChild(link);
    }

    document.body.appendChild(portal);
    activePortal = portal;

    // Position relative to the button
    var btnRect = button.getBoundingClientRect();
    var portalHeight = portal.offsetHeight;
    var viewportHeight = window.innerHeight;
    var spaceBelow = viewportHeight - btnRect.bottom;

    portal.style.left = btnRect.left + 'px';

    if (spaceBelow < portalHeight + 8) {
        // Not enough room below — show above
        portal.style.top = (btnRect.top - portalHeight - 2) + 'px';
    } else {
        // Show below
        portal.style.top = (btnRect.bottom + 2) + 'px';
    }
}

// Close portal when clicking outside
window.addEventListener('click', function (event) {
    if (!event.target.matches('.button') && !event.target.closest('.dropdown-portal')) {
        closePortal();
    }
});

// Close portal on scroll/resize so it doesn't float in the wrong spot
window.addEventListener('scroll', closePortal, true);
window.addEventListener('resize', closePortal);

/**
 * Initialize column-header sorting on the patient table.
 */
function initSorting(currentSort, currentOrder) {
    const headers = document.querySelectorAll('th[data-sort]');
    headers.forEach(function (header) {
        header.addEventListener('click', function () {
            const sortColumn = this.dataset.sort;
            let newOrder = 'asc';

            if (sortColumn === currentSort) {
                newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            }

            const url = new URL(window.location.href);
            url.searchParams.set('sort', sortColumn);
            url.searchParams.set('order', newOrder);
            window.location.href = url.toString();
        });
    });
}

/**
 * Inline editing of surgery number — click to show input.
 */
function editNumber(span) {
    const td = span.closest('.editable-number');
    const input = td.querySelector('.number-input');
    span.style.display = 'none';
    input.style.display = 'inline-block';
    input.focus();
    input.select();
}

/**
 * Save the inline surgery number via AJAX.
 */
function saveNumber(input) {
    const td = input.closest('.editable-number');
    const span = td.querySelector('.number-display');
    const patientId = td.dataset.patientId;
    const newValue = input.value.trim();

    fetch(`/update-number/${patientId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({ number: newValue }),
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                span.textContent = newValue || '—';
            } else {
                alert('Failed to update surgery number.');
            }
        })
        .catch(function () {
            alert('Error saving surgery number.');
        });

    input.style.display = 'none';
    span.style.display = 'inline';
}

/**
 * Toggle the cancelled status of a patient via AJAX.
 */
function toggleCancelled(patientId, btn) {
    fetch(`/toggle-cancelled/${patientId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                const row = btn.closest('tr');
                if (data.cancelled) {
                    btn.textContent = 'Yes';
                    btn.classList.add('cancelled-active');
                    row.classList.add('cancelled-row');
                } else {
                    btn.textContent = '';
                    btn.classList.remove('cancelled-active');
                    row.classList.remove('cancelled-row');
                }
                // Update the patient count displayed on the page
                updatePatientCount();
            }
        })
        .catch(function () {
            alert('Error toggling cancelled status.');
        });
}

/**
 * Re-count non-cancelled visible rows and update the count display.
 */
function updatePatientCount() {
    const rows = document.querySelectorAll('tbody tr');
    let count = 0;
    rows.forEach(function (row) {
        if (!row.classList.contains('cancelled-row')) {
            count++;
        }
    });
    const countEl = document.querySelector('.patient-count-value');
    if (countEl) {
        countEl.textContent = count;
    }
}

/**
 * Get the CSRF token from a meta tag or a form hidden input.
 */
function getCSRFToken() {
    // Try meta tag first
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    // Fall back to any csrf hidden input on the page
    const input = document.querySelector('input[name="csrf_token"]');
    if (input) return input.value;
    return '';
}
