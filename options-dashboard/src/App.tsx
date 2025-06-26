import React, { useEffect } from 'react'; // Add useEffect to the import
import './App.css';

function App() {
  // Add the useEffect here, inside the component function
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => console.log('API connected:', data))
      .catch(err => console.error('API connection failed:', err));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Options Dashboard</h1>
        {/* Your other JSX content */}
      </header>
    </div>
  );
}

export default App;
