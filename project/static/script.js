document.addEventListener("DOMContentLoaded", () => {
    const chartCanvas = document.getElementById("riskChart");
    if (chartCanvas && window.riskDistribution && typeof Chart !== "undefined") {
        const labels = Object.keys(window.riskDistribution);
        const values = Object.values(window.riskDistribution);

        new Chart(chartCanvas, {
            type: "doughnut",
            data: {
                labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: ["#59e6a5", "#ffc857", "#ff5d73"],
                        borderColor: ["#06111f", "#06111f", "#06111f"],
                        borderWidth: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: "#f4f7fb",
                        },
                    },
                },
                cutout: "68%",
            },
        });
    }
});
