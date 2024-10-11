// pages/api/login.js
export default (req, res) => {
    if (req.method === 'POST') {
      const { username, password } = req.body;
  
      // Perform authentication logic here
      // For simplicity, just check if the username and password are both 'demo'
      if (username === 'demo' && password === 'demo') {
        res.status(200).json({ success: true, message: 'Login successful' });
      } else {
        res.status(401).json({ success: false, message: 'Invalid credentials' });
      }
    } else {
      res.status(405).json({ success: false, message: 'Method Not Allowed' });
    }
  };
  