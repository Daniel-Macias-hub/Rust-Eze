// JavaScript para funcionalidades generales de Rust-Eze
// Este archivo define funciones globales para toda la aplicación

/**
 * Función para hacer llamadas API
 * @param {string} url - URL del endpoint
 * @param {any} data - Datos a enviar
 * @param {string} method - Método HTTP (GET, POST, etc.)
 * @returns {Promise<any>} Respuesta JSON
 */
async function apiCall(url, data, method = 'POST') {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error en API call:', error);
        return { 
            success: false, 
            message: 'Error de conexión con el servidor' 
        };
    }
}

/**
 * Mostrar notificación en pantalla
 * @param {string} message - Mensaje a mostrar
 * @param {'success'|'error'|'warning'|'info'} type - Tipo de notificación
 */
function showNotification(message, type = 'info') {
    // Crear contenedor de notificaciones si no existe
    let container = document.getElementById('notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notifications-container';
        container.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 400px;';
        document.body.appendChild(container);
    }

    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger', 
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const icon = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }[type] || 'ℹ️';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.style.marginBottom = '10px';
    notification.style.animation = 'slideInRight 0.3s ease';
    notification.innerHTML = `
        <strong>${icon}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Confirmación para acciones críticas
 * @param {string} message - Mensaje de confirmación
 * @param {Function} callback - Función a ejecutar si se confirma
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Formatear moneda
 * @param {number} amount - Cantidad a formatear
 * @returns {string} Moneda formateada
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

// ================================================
// INICIALIZACIÓN
// ================================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        // Usar bootstrap global
        if (typeof bootstrap !== 'undefined') {
            new bootstrap.Tooltip(tooltipTriggerEl);
        }
    });

    // Auto-ocultar alerts después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            if (typeof bootstrap !== 'undefined') {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Agregar estilo para animaciones de notificación
    if (!document.querySelector('#notification-styles')) {
        var style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
});

// ================================================
// MANEJO DE ERRORES GLOBAL
// ================================================

window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    if (typeof showNotification === 'function') {
        showNotification('Ocurrió un error inesperado', 'error');
    }
});

// ================================================
// HACER FUNCIONES GLOBALES
// ================================================

// Hacer funciones disponibles globalmente
window.apiCall = apiCall;
window.showNotification = showNotification;
window.confirmAction = confirmAction;
window.formatCurrency = formatCurrency;

// Para CommonJS (Node.js) - ignorar si no se usa
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiCall: apiCall,
        showNotification: showNotification,
        confirmAction: confirmAction,
        formatCurrency: formatCurrency
    };
}