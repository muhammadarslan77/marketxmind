if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register(serviceWorkerUrl)
      .then(function(registration) {
        console.log('Service Worker is registered', registration);
      })
      .catch(function(err) {
        console.error('Registration failed:', err);
      });
  });
}
