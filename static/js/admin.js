

// Dummy data for statistics
  const dummyStats = {
    totalWaste: 1520,
    recyclableWaste: 980,
    nonRecyclableWaste: 540,
  };
  
  // Render Bar and Pie Charts
  function renderCharts() {
    // Bar Chart
    const barCtx = document.getElementById("wasteBarChart").getContext("2d");
    new Chart(barCtx, {
      type: "bar",
      data: {
        labels: ["Recyclable", "Non-Recyclable"],
        datasets: [
          {
            label: "Waste Types",
            data: [dummyStats.recyclableWaste, dummyStats.nonRecyclableWaste],
            backgroundColor: ["#4caf50", "#f44336"],
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
  
    // Pie Chart
    const pieCtx = document.getElementById("wastePieChart").getContext("2d");
    new Chart(pieCtx, {
      type: "pie",
      data: {
        labels: ["Recyclable", "Non-Recyclable"],
        datasets: [
          {
            data: [dummyStats.recyclableWaste, dummyStats.nonRecyclableWaste],
            backgroundColor: ["#4caf50", "#f44336"],
          },
        ],
      },
      options: {
        responsive: true,
      },
    });
  }
  
  // Populate statistics section with dummy data
  function populateStatistics() {
    document.getElementById("totalWaste").innerText = dummyStats.totalWaste;
    document.getElementById("recyclableWaste").innerText =
      dummyStats.recyclableWaste;
    document.getElementById("nonRecyclableWaste").innerText =
      dummyStats.nonRecyclableWaste;
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Fetch users when the View Users modal is triggered
    document.getElementById('viewUsersBtn').addEventListener('click', function () {
        fetch('/api/users')
            .then(response => response.json())
            .then(data => {
                // Populate the users table with the data from the backend
                const usersTable = document.getElementById('usersTable');
                usersTable.innerHTML = '';  // Clear existing content

                if (data.error) {
                    alert(data.error);
                } else {
                    // Populate the table with users
                    data.forEach((user, index) => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${user.email}</td>
                            <td>${user.role}</td>
                        `;
                        usersTable.appendChild(row);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching users:', error);
                alert('An error occurred while fetching users.');
            });
    });
});

    // Remove user when form is submitted
    document.getElementById('removeUserForm').addEventListener('submit', function(e) {
      e.preventDefault();
      const email = document.getElementById('userEmail').value;
      removeUser(email);
    });


  // Function to remove a user
  function removeUser(email) {
    if (email) {
      fetch(`/api/users?email=${email}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(response => response.json())
      .then(data => {
        alert(data.message || data.error);
        if (data.message) {
          // Optionally, you can refresh the list of users
          fetchUsers();
        }
      })
      .catch(error => {
        console.error('Error removing user:', error);
      });
    }
  }
  
  // Initialize statistics and charts
  populateStatistics();
  renderCharts();
  