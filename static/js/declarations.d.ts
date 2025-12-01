// Declaraciones de tipo para funciones globales

declare global {
    interface Window {
        apiCall: (url: string, data?: any, method?: string) => Promise<any>;
        showNotification: (message: string, type?: 'success'|'error'|'warning'|'info') => void;
        confirmAction: (message: string, callback: () => void) => void;
        formatCurrency: (amount: number) => string;
    }
    
    var apiCall: Window['apiCall'];
    var showNotification: Window['showNotification'];
    var confirmAction: Window['confirmAction'];
    var formatCurrency: Window['formatCurrency'];
}

export {};