
  document.getElementById('signupForm').addEventListener('submit', function (event) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email.includes('@')) {
      alert('Please enter a valid email address.');
      event.preventDefault();
      return;
    }

    if (password.length < 6) {
      alert('Password must be at least 6 characters long.');
      event.preventDefault();
    }
  });

