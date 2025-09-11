window.App = window.App || {};

App.editPage = {
    init: function() {
        const editCheckboxes = document.querySelectorAll('.edit-checkbox');
        if (editCheckboxes.length > 0) {
            editCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const row = this.closest('tr');
                    const inputs = row.querySelectorAll('input[type="date"], input[type="number"], input[type="text"], select');
                    inputs.forEach(input => {
                        input.disabled = !this.checked;
                    });
                });
            });
        }
    }
};