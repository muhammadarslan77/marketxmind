(function () {
  'use strict';

  // Dark Mode
  var toggleSwitch = document.getElementById('darkSwitch');
  var currentTheme = localStorage.getItem('theme');

  if (currentTheme) {
    document.documentElement.setAttribute('theme-color', currentTheme);
    if (currentTheme === 'dark') {
      if (toggleSwitch) {
        toggleSwitch.checked = true;
      }
    }
  }

  function switchTheme(e) {
    if (e.target.checked) {
      document.documentElement.setAttribute('theme-color', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.setAttribute('theme-color', 'light');
      localStorage.setItem('theme', 'light');
    }
  }

  if (toggleSwitch) {
    toggleSwitch.addEventListener('change', switchTheme, false);
  }

  // RTL MODE CODE
  var rtltoggleSwitch = document.getElementById("rtlSwitch");
  var rtlcurrentTheme = localStorage.getItem("view");

  if (rtlcurrentTheme) {
    document.documentElement.setAttribute("view-mode", rtlcurrentTheme);
    if (rtlcurrentTheme === "rtl") {
      if (rtltoggleSwitch) {
        rtltoggleSwitch.checked = true;
      }
    }
  }

  function rtlswitchTheme(e) {
    if (e.target.checked) {
      document.documentElement.setAttribute("view-mode", "rtl");
      localStorage.setItem("view", "rtl");
    } else {
      document.documentElement.setAttribute("view-mode", "ltr");
      localStorage.setItem("view", "ltr");
    }
  }

  if (rtltoggleSwitch) {
    rtltoggleSwitch.addEventListener("change", rtlswitchTheme, false);
  }

})();