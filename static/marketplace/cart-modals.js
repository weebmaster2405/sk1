// Cart Modal Functionality
// This file provides modal functionality for cart operations

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show shopping cart delete confirmation modal
function showShoppingCartDeleteModal(chartId, chartName) {
    $('#shoppingCartItemName').text(chartName);
    $('#confirmShoppingCartDeleteBtn').data('chart-id', chartId);
    $('#confirmShoppingCartDeleteModal').modal('show');
}

// Show toast notification
function showToast(type, message) {
    var bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    var toastHtml = `
        <div class="toast" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 1050;">
            <div class="toast-header ${bgClass} text-white">
                <strong class="mr-auto">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                    ${type === 'success' ? 'Success' : 'Error'}
                </strong>
                <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast">
                    <span>&times;</span>
                </button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    $('body').append(toastHtml);
    $('.toast').last().toast({delay: 3000}).toast('show');
    
    // Remove toast after it's hidden
    $('.toast').last().on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// Initialize cart modal functionality when document is ready
$(document).ready(function() {
    // Handle shopping cart delete confirmation
    $(document).on('click', '#confirmShoppingCartDeleteBtn', function() {
        var chartId = $(this).data('chart-id');
        var button = $(this);
        
        // Disable button during request
        button.prop('disabled', true);
        button.html('<i class="material-icons" style="animation: spin 1s linear infinite; font-size: 1rem; margin-right: 0.5rem;">refresh</i> Removing...');
        
        $.ajax({
            url: '/cart/remove/' + chartId + '/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                if (response.success) {
                    // Show success message
                    showToast('success', '✓ Item has been successfully removed from your cart!');
                    
                    // Reload the page to refresh cart contents
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', 'Error removing item from cart: ' + response.message);
                }
            },
            error: function() {
                showToast('error', 'Error removing item from cart. Please try again.');
            },
            complete: function() {
                button.prop('disabled', false);
                button.html('<i class="material-icons" style="font-size: 1rem; margin-right: 0.5rem;">remove_shopping_cart</i> Remove from Cart');
                $('#confirmShoppingCartDeleteModal').modal('hide');
            }
        });
    });
});

// Make functions globally available
window.showShoppingCartDeleteModal = showShoppingCartDeleteModal;
window.showToast = showToast;
