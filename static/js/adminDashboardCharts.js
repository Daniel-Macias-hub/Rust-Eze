(function () {
    const dataContainer = document.getElementById('dashboard-data');
    if (!dataContainer || typeof Chart === 'undefined') {
        return;
    }

    const parse = (value, fallback) => {
        try {
            if (!value) return fallback;
            return JSON.parse(value);
        } catch (e) {
            return fallback;
        }
    };

    const ventasLabels = parse(dataContainer.dataset.ventasLabels, []);
    const ventasData = parse(dataContainer.dataset.ventasValores, []);
    const topLabels = parse(dataContainer.dataset.topLabels, []);
    const topData = parse(dataContainer.dataset.topValores, []);

    // Ajustes globales de Chart.js para modo oscuro
    Chart.defaults.color = '#e5e7eb';
    Chart.defaults.font.family = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

    const chartVentasCanvas = document.getElementById('chartVentasMes');
    const chartTopCanvas = document.getElementById('chartTopModelos');

    // ==========================
    // LÍNEA: VENTAS POR MES
    // ==========================
    if (chartVentasCanvas && ventasLabels.length && ventasData.length) {
        const ctx = chartVentasCanvas.getContext('2d');

        const gradient = ctx.createLinearGradient(0, 0, 0, chartVentasCanvas.height);
        gradient.addColorStop(0, 'rgba(56, 189, 248, 0.55)');
        gradient.addColorStop(1, 'rgba(15, 23, 42, 0.0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ventasLabels,
                datasets: [{
                    label: 'Ventas ($)',
                    data: ventasData,
                    tension: 0.35,
                    borderWidth: 2,
                    borderColor: '#38bdf8',
                    backgroundColor: gradient,
                    fill: true,
                    pointRadius: 3.5,
                    pointBackgroundColor: '#38bdf8',
                    pointBorderColor: '#0f172a',
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e5e7eb' }
                    },
                    tooltip: {
                        backgroundColor: '#020617',
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        titleColor: '#f9fafb',
                        bodyColor: '#e5e7eb'
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(55,65,81,0.4)' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(55,65,81,0.3)' }
                    }
                }
            }
        });
    }

    // ==========================
    // BARRAS: TOP MODELOS
    // ==========================
    if (chartTopCanvas && topLabels.length && topData.length) {
        const ctx2 = chartTopCanvas.getContext('2d');

        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: topLabels,
                datasets: [{
                    label: 'Unidades vendidas',
                    data: topData,
                    borderWidth: 1,
                    borderRadius: 6,
                    backgroundColor: [
                        'rgba(94, 234, 212, 0.7)',
                        'rgba(129, 140, 248, 0.7)',
                        'rgba(251, 113, 133, 0.7)',
                        'rgba(253, 224, 71, 0.7)',
                        'rgba(96, 165, 250, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#020617',
                        borderColor: '#4f46e5',
                        borderWidth: 1,
                        titleColor: '#f9fafb',
                        bodyColor: '#e5e7eb'
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#9ca3af', font: { size: 10 } },
                        grid: { display: false }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(55,65,81,0.3)' }
                    }
                }
            }
        });
    }
})();
