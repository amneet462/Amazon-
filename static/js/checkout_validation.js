document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('checkout-form');
    
    // Validate expiration date
    function isValidExpiration(exp) {
        if (!/^(0[1-9]|1[0-2])\/([0-9]{2})$/.test(exp)) {
            return false;
        }
        const [month, year] = exp.split('/');
        const expDate = new Date(2000 + parseInt(year), parseInt(month) - 1);
        const today = new Date();
        return expDate > today;
    }

    // Validate ZIP code (US format)
    function isValidZip(zip) {
        return /^\d{6}$/.test(zip);
    }

    // Validate state (US states)
    function isValidState(state) {
        const states =  [
            'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 
        'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 
        'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 
        'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 
        'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 
        'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 
        'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 
        'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 
        'Puducherry'
        ]
    
        return states.includes(state.toUpperCase());
    }

    // Add event listeners for real-time validation
    document.getElementById('zip').addEventListener('input', function(e) {
        const isValid = isValidZip(e.target.value);
        this.classList.toggle('is-invalid', !isValid);
        if (!isValid) {
            this.setCustomValidity('Please enter a valid ZIP code (e.g., 123456 )');
        } else {
            this.setCustomValidity('');
        }
    });

    document.getElementById('state').addEventListener('input', function(e) {
        const isValid = isValidState(e.target.value);
        this.classList.toggle('is-invalid', !isValid);
        if (!isValid) {
            this.setCustomValidity('Please enter a valid two-letter state code (e.g., CA)');
        } else {
            this.setCustomValidity('');
        }
    });

    document.getElementById('cc-expiration').addEventListener('input', function(e) {
        const isValid = isValidExpiration(e.target.value);
        this.classList.toggle('is-invalid', !isValid);
        if (!isValid) {
            this.setCustomValidity('Please enter a valid future date in MM/YY format');
        } else {
            this.setCustomValidity('');
        }
    });

    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate all fields
        const zip = document.getElementById('zip').value;
        const state = document.getElementById('state').value;
        const expiration = document.getElementById('cc-expiration').value;
        
        if (!isValidZip(zip)) {
            alert('Please enter a valid ZIP code');
            return;
        }
        
        if (!isValidState(state)) {
            alert('Please enter a valid state code');
            return;
        }
        
        if (!isValidExpiration(expiration)) {
            alert('Please enter a valid expiration date');
            return;
        }

        // If all validations pass, submit the form
        this.submit();
    });
});
