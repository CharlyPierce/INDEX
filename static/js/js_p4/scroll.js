// Variable para determinar si se está desplazando
var scrolling = false;

// Manejo del desplazamiento con base en la posición del mouse en la ventana
$(document).mousemove(function(e) {
    var windowWidth = $(window).width();
    var sixthPart = windowWidth / 6;

    var mouseX = e.pageX;
    var $scrollableElement = $('.desplazamiento');

    if (mouseX < sixthPart) {
        if (!scrolling) {
            console.log('Inicio de desplazamiento a la izquierda');
            scrolling = true;
            $scrollableElement.stop().animate({scrollLeft: '-=350'}, 2000, function() {
                scrolling = false;
            });
        }
    } else if (mouseX > windowWidth - sixthPart) {
        if (!scrolling) {
            console.log('Inicio de desplazamiento a la derecha');
            scrolling = true;
            $scrollableElement.stop().animate({scrollLeft: '+=350'}, 1000, function() {
                scrolling = false;
            });
        }
    } else {
        if (scrolling) {
            console.log('Detención de desplazamiento');
            $scrollableElement.stop();
            scrolling = false;
        }
    }
});

// Detener el desplazamiento cuando el mouse ingresa a ciertos elementos
$(".desplazamiento, .lista-tema .tema-lista .lista-subtema").mouseenter(function() {
    if (scrolling) {
        console.log('Detención de desplazamiento por mouseenter');
        $('.desplazamiento').stop();
        scrolling = false;
    }
});





// Iniciar el desplazamiento hacia el inicio de la página cuando el mouse sale de ciertos elementos
var timeoutId;

	$(".desplazamientos").on('mouseleave', function() {
		clearTimeout(timeoutId);

		if (!scrolling) {
			console.log('Inicio de desplazamiento a la izquierda por mouseleave');
			scrolling = true;
			$('.desplazamiento').stop().animate({scrollLeft: 0}, 2000, function() {
				scrolling = false;
			});
		}
	});

	$(".desplazamientos").on('mousemove', function(e) {
		clearTimeout(timeoutId);

		if (!$(e.target).closest('.lista-tema .tema-lista .lista-subtema').length) {
			timeoutId = setTimeout(function() {
				if (!scrolling) {
					console.log('Inicio de desplazamiento a la izquierda por inactividad');
					scrolling = true;
					$('.desplazamiento').stop().animate({scrollLeft: 0}, 2000, function() {
						scrolling = false;
					});
				}
			}, 3000); // Tiempo de inactividad después del cual se ejecutará la función (en milisegundos)
		}
	});

	$(window).on('mouseout', function(e) {
		clearTimeout(timeoutId);

		var toElement = e.toElement || e.relatedTarget;
		var isLeavingBrowser = !toElement || toElement.nodeName === "HTML";

		if (isLeavingBrowser && !scrolling && !$('.desplazamiento').closest('.lista-tema .tema-lista .lista-subtema').length) {
			console.log('Inicio de desplazamiento a la izquierda por salir del alcance del navegador');
			scrolling = true;
			$('.desplazamiento').stop().animate({scrollLeft: 0}, 1000, function() {
				scrolling = false;
			});
		}
	});

	document.addEventListener('visibilitychange', function() {
		if (document.visibilityState === 'hidden' && !scrolling && !$('.desplazamiento').closest('.lista-tema .tema-lista .lista-subtema').length) {
			console.log('Inicio de desplazamiento a la izquierda por cambio de visibilidad');
			scrolling = true;
			$('.desplazamiento').stop().animate({scrollLeft: 0}, 1000, function() {
				scrolling = false;
			});
		}
	});

	window.addEventListener('beforeunload', function() {
		if (!scrolling && !$('.desplazamiento').closest('.lista-tema .tema-lista .lista-subtema').length) {
			console.log('Inicio de desplazamiento a la izquierda antes de cerrar la página');
			scrolling = true;
			$('.desplazamiento').stop().animate({scrollLeft: 0}, 1000, function() {
				scrolling = false;
			});
		}
	});


