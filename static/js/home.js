  // Show login prompt if user is not logged in
  function promptLogin() {
    alert("You must log in first.");
  }
  
  // Disable camera access and capture button if user is not logged in
  function checkLoginStatus() {
    const authToken = localStorage.getItem("authToken");
  
    if (!authToken) {
      // Disable the camera and capture button if the user is not logged in
      document.getElementById("cameraStream").style.display = "none"; // Hide the camera stream
      document.getElementById("captureBtn").disabled = true; // Disable the capture button
      alert("You must be logged in to capture an image.");
    } else {
      // Enable the camera and capture button if the user is logged in
      document.getElementById("cameraStream").style.display = "block"; // Show the camera stream
      document.getElementById("captureBtn").disabled = false; // Enable the capture button
    }
  }
  
  // Check login status when the page loads
  checkLoginStatus();
  
  // Capture Button
  document.getElementById("captureBtn").addEventListener("click", function () {
    const authToken = localStorage.getItem("authToken");
  
    // Check if the user is logged in before allowing image capture
    if (!authToken) {
      alert("You must be logged in to classify an image.");
      return; // Prevent further action if not logged in
    }
  
    const video = document.getElementById("cameraStream");
    const canvas = document.getElementById("snapshot");
    const context = canvas.getContext("2d");
  
    // Set canvas size to match the video stream
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  
    // Draw the current video frame to the canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
  
    // Convert the canvas to a blob (image)
    canvas.toBlob(async function (blob) {
      const formData = new FormData();
      formData.append("image", blob, "snapshot.jpg"); // Append the image to form data
  
      try {
        // Send the image to the backend
        const response = await fetch("/upload_image", {
          method: "POST",
          body: formData,
        });
  
        const textData = await response.text(); // Read the response as plain text
  
        // Debugging: log the raw response
        console.log("Server Response: ", textData);
  
        // If response is empty, throw an error
        if (!textData) {
          throw new Error("Empty response from server");
        }
  
        // Try to parse the response as JSON
        const data = JSON.parse(textData);
  
        if (response.ok) {
          // Show result in the UI only if the image upload is successful
          document.getElementById("categoryResult").innerText = data.category;
          document.getElementById("confidenceResult").innerText =
            (data.confidence * 100).toFixed(2) + "%";
  
          // Dynamically add the image to the classification table
          const imgElement = document.createElement("img");
          imgElement.src = data.image_url; // URL of the uploaded image
          imgElement.alt = "Uploaded Image";
          imgElement.width = 100; // Image size
          imgElement.height = 100;
  
          // Add the new row to the history table
          const historyTable = document
            .getElementById("historyTable")
            .getElementsByTagName("tbody")[0];
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${data.id}</td>
            <td>${data.category}</td>
            <td>${data.confidence}</td>
            <td>${data.timestamp}</td>
            <td><img src="${data.image_url}" width="100" height="100" alt="Uploaded Image"></td>
          `;
          historyTable.appendChild(row);
  
          // Show success message after successful image upload
          alert("Image captured successfully!");
  
          // Refresh statistics and history after successful upload
          populateStatistics();
          populateHistory();
        } else {
          // If there is an error with the image upload, show an error message
          alert("Error: " + data.error);
        }
      } catch (error) {
        // If an error occurs during the fetch, show a message
        alert("Error uploading image: " + error.message);
      }
    });
  });
