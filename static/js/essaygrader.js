document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("essay-form");
  const gradeLevelElement = document.getElementById("grade-level");
  const gradePercentageElement = document.getElementById("grade-percentage");
  const readabilityScoreElement = document.getElementById("readability-score");
  const fkGradeElement = document.getElementById("fk-grade");
  const feedbackListElement = document.getElementById("feedback-list");

  form.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.grade_level !== undefined) {
          // Update grade, readability score, Flesch-Kincaid grade, and feedback sections with data from the server
          gradeLevelElement.textContent = data.grade_level;
          gradePercentageElement.textContent = data.grade_percentage + "%";
          readabilityScoreElement.textContent = data.readability_score;
          fkGradeElement.textContent = data.fk_grade;

          feedbackListElement.innerHTML = data.suggestions
            .map((suggestion) => `<li>${suggestion}</li>`)
            .join("");
        } else {
          // Handle errors if any
          gradeLevelElement.textContent = "Error";
          gradePercentageElement.textContent = "";
          readabilityScoreElement.textContent = "";
          fkGradeElement.textContent = "";
          feedbackListElement.innerHTML =
            "<li>An error occurred. Please try again.</li>";
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        gradeLevelElement.textContent = "Error";
        gradePercentageElement.textContent = "";
        readabilityScoreElement.textContent = "";
        fkGradeElement.textContent = "";
        feedbackListElement.innerHTML =
          "<li>An error occurred. Please try again.</li>";
      });
  });
});
