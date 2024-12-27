
  document.getElementById('loginForm').addEventListener('submit', function (event) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email.includes('@')) {
      alert('Please enter a valid email address.');
      event.preventDefault();
    }
  });

