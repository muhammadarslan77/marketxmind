(function () {
    'use strict';

    const intStatus = document.getElementById('internetStatus');
    const backText = 'Your internet connection is back';
    const lostText = 'Oops! No internet connection.';
    const successColor = '#00b894';
    const failureColor = '#ea4c62';

    if (window.navigator.onLine) {
        intStatus.textContent = backText;
        intStatus.style.backgroundColor = successColor;
        intStatus.style.display = 'none';
    } else {
        intStatus.textContent = lostText;
        intStatus.style.backgroundColor = failureColor;
        intStatus.style.display = 'block';
    }

    window.addEventListener('online', function () {
        intStatus.textContent = backText;
        intStatus.style.backgroundColor = successColor;
        intStatus.style.display = 'block';
        var hideTime = setTimeout( function() {
            intStatus.style.display = 'none';
        }, 5000);
    });

    window.addEventListener('offline', function () {
        intStatus.textContent = lostText;
        intStatus.style.backgroundColor = failureColor;
        intStatus.style.display = 'block';
    });

})();