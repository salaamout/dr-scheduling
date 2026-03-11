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
 * Toggle a print dropdown menu and close any other open menus.
 */
function togglePrintMenu(patientId) {
    const menu = document.getElementById(`printMenu${patientId}`);
    const dropdowns = document.getElementsByClassName('dropdown-content');

    // Close all other dropdowns
    for (const dropdown of dropdowns) {
        if (dropdown !== menu && dropdown.style.display === 'block') {
            dropdown.style.display = 'none';
        }
    }

    // Toggle the clicked dropdown
    if (menu.style.display === 'block') {
        menu.style.display = 'none';
        menu.style.top = '';
        menu.style.bottom = '';
    } else {
        const button = menu.previousElementSibling;
        const buttonRect = button.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const spaceBelow = viewportHeight - buttonRect.bottom;
        const menuHeight = 120;
        const inBottomThird = buttonRect.bottom > (viewportHeight * 0.67);

        if (spaceBelow < menuHeight || inBottomThird) {
            menu.style.bottom = '100%';
            menu.style.top = 'auto';
        } else {
            menu.style.top = '100%';
            menu.style.bottom = 'auto';
        }

        menu.style.display = 'block';
    }
}

// Close all dropdowns when clicking outside
window.addEventListener('click', function (event) {
    if (!event.target.matches('.button')) {
        const dropdowns = document.getElementsByClassName('dropdown-content');
        for (const dropdown of dropdowns) {
            if (dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            }
        }
    }
});

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
