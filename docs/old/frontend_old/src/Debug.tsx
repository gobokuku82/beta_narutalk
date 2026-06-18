import { useLocation } from 'react-router-dom';

export const Debug = () => {
  const location = useLocation();

  console.log('Debug Component Rendered');
  console.log('Location:', location);

  return (
    <div className="p-4 bg-yellow-100">
      <h1>Debug Info</h1>
      <p>Path: {location.pathname}</p>
      <p>React App is working!</p>
    </div>
  );
};