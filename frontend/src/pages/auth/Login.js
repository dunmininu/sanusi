// pages/login.js
import { useState } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';

const fetchUser = async (username) => {
  const { data } = await axios.get(`/api/user/${username}`);
  return data;
};

const loginUser = async (credentials) => {
  const { data } = await axios.post('/api/login', credentials);
  return data;
};

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const { data: user } = useQuery(['user', username], () => fetchUser(username), {
    enabled: !!username,c
  });

  const handleLogin = async () => {
    const credentials = { username, password };
    // Assuming your login endpoint is '/api/login'
    const result = await loginUser(credentials);
    // Handle authentication result
    console.log(result);
  };

  return (
    <div>
      <h1>Login</h1>
      <div>
        <label>
          Username:
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Password:
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
      </div>
      <button onClick={handleLogin}>Login</button>

      {user && (
        <div>
          <h2>User Details</h2>
          <p>Username: {user.username}</p>
          <p>Email: {user.email}</p>
        </div>
      )}
    </div>
  );
};

export default Login;
