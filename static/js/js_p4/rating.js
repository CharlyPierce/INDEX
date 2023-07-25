$(document).ready(function() {
    $('.contenedor-calificacion').each(function() {
        var contenedor = $(this);
        var tema = contenedor.find('.estrella').data('tema');
        var clave = contenedor.find('.estrella').data('clave');
        var calificacion_usuario = contenedor.data('calificacion-usuario');


        contenedor.find('.estrella').click(function() {
            var calificacion = $(this).data('rating');

            // Añadimos una alerta con los valores de las variables
            //alert("tema: " + tema + ", padre: " + padre + ", clave: " + clave + ", calificacion: " + calificacion);

            // Si la calificación es la misma que calificacion_usuario, no haga nada
            if (calificacion == calificacion_usuario) {
                return;
            }

            $.ajax({
                url: "/page7/" + clave,
                type: "POST",
                contentType: 'application/json',  // especifica que estás enviando JSON
                data: JSON.stringify({
                    calificacion: calificacion,
                    tema: tema,
                }),
                success: function(response) {
                    window.location.href = "/page4/" + clave;
                },
                error: function(error) {
                    console.log(error);
                }
            });
            
        });
    });
});

