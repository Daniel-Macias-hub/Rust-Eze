(function () {
    const el = document.getElementById('dashboard-data');

    const parse = (value, fallback) => {
        try {
            if (!value) return fallback;
            return JSON.parse(value);
        } catch (e) {
            return fallback;
        }
    };

    const ventasLabels = parse(el?.dataset.ventasLabels, []);
    const ventasData = parse(el?.dataset.ventasValores, []);
    const topLabels = parse(el?.dataset.topLabels, []);
    const topData = parse(el?.dataset.topValores, []);

    const chartVentasCanvas = document.getElementById('chartVentasMes');
    const chartTopCanvas = document.getElementById('chartTopModelos');

    if (chartVentasCanvas && ventasLabels.length && ventasData.length) {
        const ctx = chartVentasCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ventasLabels,
                datasets: [{
                    label: 'Ventas ($)',
                    data: ventasData,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#e5e7eb' } }
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

    if (chartTopCanvas && topLabels.length && topData.length) {
        const ctx2 = chartTopCanvas.getContext('2d');
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: topLabels,
                datasets: [{
                    label: 'Unidades vendidas',
                    data: topData,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
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
