$(document).ready(function () {
  $(".summarize").on("click", function (e) {
    e.preventDefault();

    var inputText = $("#rawtext").val();

    if (inputText.trim() === "") {
      alert("Please enter some text to summarize.");
      return;
    }

    $.ajax({
      url: "/comparer",
      type: "POST",
      contentType: "application/x-www-form-urlencoded",
      data: { rawtext: inputText },
      success: function (response) {
        // Clear previous results
        $(".compare-input-text p").text("");
        $(".algo-box p").text("No summary available.");
        $(".reading p").text("");

        // Update the compare-input-text with input text
        $(".compare-input-text p").text(inputText);

        // Iterate through each .algo-box
        $(".algo-box").each(function (index) {
          var algoBox = $(this);
          var readingElement = algoBox.next(".reading");

          switch (index) {
            case 0:
              algoBox
                .find("p")
                .text(response.final_summary_gpt || "No summary available.");
              readingElement
                .find("p")
                .eq(0)
                .text(
                  "Reading Time: " +
                    (response.summary_reading_time_gpt || "N/A") +
                    " Minutes"
                );
              readingElement
                .find("p")
                .eq(1)
                .text(
                  "Time Elapsed: " +
                    (response.processing_time_gpt || "N/A") +
                    " Seconds"
                );
              break;
            case 1:
              algoBox
                .find("p")
                .text(response.final_summary_nltk || "No summary available.");
              readingElement
                .find("p")
                .eq(0)
                .text(
                  "Reading Time: " +
                    (response.summary_reading_time_nltk || "N/A") +
                    " Minutes"
                );
              readingElement
                .find("p")
                .eq(1)
                .text(
                  "Time Elapsed: " +
                    (response.processing_time_nltk || "N/A") +
                    " Seconds"
                );
              break;
            case 2:
              algoBox
                .find("p")
                .text(response.final_summary_spacy || "No summary available.");
              readingElement
                .find("p")
                .eq(0)
                .text(
                  "Reading Time: " +
                    (response.summary_reading_time_spacy || "N/A") +
                    " Minutes"
                );
              readingElement
                .find("p")
                .eq(1)
                .text(
                  "Time Elapsed: " +
                    (response.processing_time_spacy || "N/A") +
                    " Seconds"
                );
              break;
            case 3:
              algoBox
                .find("p")
                .text(response.final_summary_luhn || "No summary available.");
              readingElement
                .find("p")
                .eq(0)
                .text(
                  "Reading Time: " +
                    (response.summary_reading_time_luhn || "N/A") +
                    " Minutes"
                );
              readingElement
                .find("p")
                .eq(1)
                .text(
                  "Time Elapsed: " +
                    (response.processing_time_luhn || "N/A") +
                    " Seconds"
                );
              break;
            default:
              console.log("Unexpected index:", index);
          }
        });
      },
      error: function (error) {
        alert(
          "An error occurred while processing your request. Please try again."
        );
        console.log("Error:", error);
      },
    });
  });
});
