function showSectionContent(sectionId) {
  // Hide all tab sections
  var tabSections = document.getElementsByClassName("tab-section");// section pai
  for (var i = 0; i < tabSections.length; i++) {
    tabSections[i].classList.remove("active");
  }

  // Show the clicked tab section
  document.getElementById("section" + sectionId).classList.add("active");
}
