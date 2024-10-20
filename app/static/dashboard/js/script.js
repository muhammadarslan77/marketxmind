const designDropDown = document.getElementById('design');
const colorDropDown = document.getElementById('color');
const otherJobRole = document.getElementById("other-job-role");
const jobTitles = document.getElementById('title');


jobTitles.addEventListener('change', function () {
  if (this.value === 'other') {
    otherJobRole.style.display = "block";
    // console.log('You selected: ', this.value);
  }

  if (this.value !== 'other') {
    otherJobRole.style.display = "none";
  }
});

// Places t-shirt color menu inside variable & Turns off the t-shirt color options dropdown menu
colorDropDown.disabled = true;

// console.log(document.getElementById('color').options);


// This function adds a listener to the Design dropdown menu. 
// When it changes, it activates the t-shirt menu and gives the
// appropriate choices
designDropDown.addEventListener('change', e => {
  colorDropDown.disabled = false;

  for (let i = 0; i < colorDropDown.length; i++) {
    let shirtOption = colorDropDown[i].value;
    let selectedShirt = e.target.value;
  }

  let designChoice = e.target.value;

  if (designChoice === 'js puns') {
    //PROGRESS
    for (let i = 0; i < colorDropDown.length; i++) {
      let punShirts = colorDropDown[i].dataset.theme === 'js puns';
      let heartShirts = colorDropDown[i].dataset.theme === 'heart js';
      if (colorDropDown[i].dataset.theme === 'heart js') {
        colorDropDown[i].disabled = true;
      }
    }
    // console.log(colorDropDown.value);
  }

   if (designChoice === 'heart js') {
    for (let i = 0; i < colorDropDown.length; i++) {
      if (colorDropDown[i].dataset.theme === 'js puns') {
        colorDropDown[i].disabled = true;
      }
    }

    // console.log(colorDropDown[2].dataset.theme);

  }
});



colorDropDown.addEventListener('change', e => {

  for (let i = 0; i < colorDropDown.length; i++) {
    let shirtOption = colorDropDown[i].value;
    let selectedShirt = e.target.value;

    if (selectedShirt === shirtOption) {
      console.log(`Your choice was ${selectedShirt} and you got ${shirtOption}`)
    }
  }
})


// if (this.value === "js puns") {

//   //This logic grabs only the menu items that pertain to puns
//   const punsOptions = document.querySelectorAll('[data-theme="js puns"]');
//   console.log(punsOptions)

// }

// if (this.value === "heart js") {

//   //This logic grabs only the menu items that pertain to heart js
//   const heartOptions = document.querySelectorAll('[data-theme="heart js"]')
//   console.log(heartOptions)

// }

// const choices = jobTitles.querySelectorAll("option");

// console.log(tShirtColor[3]);
// console.log(designDropDown[1]);