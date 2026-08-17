/**
 * Buscador de clanes: enfoca el input y resalta jugadores coincidentes.
 */
(function () {
    'use strict';

    var searchInput = document.getElementById('clans-search');
    if (searchInput) {
        searchInput.focus();
        if (searchInput.value !== '') {
            searchInput.select();
        }
    }

    var hits = document.querySelectorAll('tr.is-search-hit');
    if (!hits.length) {
        return;
    }

    // Lleva al primer resultado y deja el parpadeo CSS unos segundos.
    hits[0].scrollIntoView({ behavior: 'smooth', block: 'center' });

    window.setTimeout(function () {
        for (var i = 0; i < hits.length; i++) {
            hits[i].classList.add('is-search-hit--done');
        }
    }, 4500);
})();
