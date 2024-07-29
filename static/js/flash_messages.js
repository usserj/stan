document.addEventListener("DOMContentLoaded", function() {
    // Hacer que los mensajes flash desaparezcan automáticamente después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var closeButton = alert.querySelector('button.close');
            if (closeButton) {
                closeButton.click();
            }
        });
    }, 5000); // 5000 milisegundos = 5 segundos
});
