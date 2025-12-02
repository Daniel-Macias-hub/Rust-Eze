// Importar Bootstrap si se usa como módulo
import 'bootstrap';

// Exportar funciones globales
export { apiCall, showNotification, confirmAction, formatCurrency };

// También hacerlas globales
if (typeof window !== 'undefined') {
    window.apiCall = apiCall;
    window.showNotification = showNotification;
    window.confirmAction = confirmAction;
    window.formatCurrency = formatCurrency;
}