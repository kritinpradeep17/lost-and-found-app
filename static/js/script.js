// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const burger = document.querySelector('.burger');
    const navLinks = document.querySelector('.nav-links');
    
    if (burger && navLinks) {
        burger.addEventListener('click', function() {
            navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', function() {
                navLinks.style.display = 'none';
            });
        });
    }
    
    // Date inputs - set max date to today
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        input.setAttribute('max', today);
    });
    
    // Image preview for file uploads
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            const previewId = `${input.id}-preview`;
            let previewElement = document.getElementById(previewId);
            
            // Create preview element if it doesn't exist
            if (!previewElement) {
                previewElement = document.createElement('div');
                previewElement.id = previewId;
                previewElement.style.marginTop = '10px';
                input.parentNode.insertBefore(previewElement, input.nextSibling);
            }
            
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '200px';
                img.style.maxHeight = '200px';
                img.style.borderRadius = '5px';
                
                // Clear previous preview
                previewElement.innerHTML = '';
                previewElement.appendChild(img);
            };
            
            reader.readAsDataURL(file);
        });
    });
});