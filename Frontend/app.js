// Escuchamos el evento de "submit" del formulario
document.getElementById('materaForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const especie = document.getElementById('especie').value;
    const humedad = parseFloat(document.getElementById('humedad').value);
    const luz = parseFloat(document.getElementById('luz').value);
    const temperatura = parseFloat(document.getElementById('temperatura').value);

    const requestData = {
        especie: especie,
        humedad: humedad,
        luz: luz,
        temperatura: temperatura
    };

    try {

        const response = await fetch('http://127.0.0.1:5000/api/v1/evaluar', {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (response.ok) {
            // Caso de éxito: Mostrar los resultados en pantalla
            document.getElementById('resultado').classList.remove('oculto');
            document.getElementById('res-nivel').innerText = `Vitalidad: ${data.nivel_vitalidad} (${data.porcentaje_vitalidad}%)`;
            document.getElementById('res-mensaje').innerText = data.mensaje;
            
            // Animamos la barra de progreso
            const barra = document.getElementById('res-barra');
            // Damos un pequeño retraso para que la animación CSS se vea fluida al asignar el nuevo ancho
            setTimeout(() => {
                barra.style.width = `${data.porcentaje_vitalidad}%`;
                // Si la vitalidad es mayor a 70 es verde, si es media es naranja, si es baja es rojo
                if (data.porcentaje_vitalidad >= 70) {
                    barra.style.backgroundColor = '#4ade80'; // Verde
                } else if (data.porcentaje_vitalidad >= 50) {
                    barra.style.backgroundColor = '#facc15'; // Amarillo/Naranja
                } else {
                    barra.style.backgroundColor = '#ef4444'; // Rojo
                }
            }, 50);
            
        } else {
            // Manejo de errores 400 o 404 del backend
            alert(`Error: ${data.error}`);
        }

    } catch (error) {
        // Error de red (ej. Backend apagado o error de CORS)
        console.error("Hubo un error de conexión:", error);
        alert("Error de conexión con el servidor de la Matera. Verifica que Flask esté corriendo.");
    }
});
