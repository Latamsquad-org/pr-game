/**
 * UX mínima del ranking: enfoca el campo de búsqueda al cargar la página.
 */
(function () {
    'use strict';

    var searchInput = document.getElementById('ranking-search');
    if (!searchInput) {
        return;
    }

    searchInput.focus();

    if (searchInput.value !== '') {
        searchInput.select();
    }
})();
