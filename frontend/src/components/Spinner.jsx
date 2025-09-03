import React from 'react';
import naruGif from '../assets/naru.gif';

const Spinner = ({ show, text = '처리 중...' }) => {
  if (!show) return null;

  return (
    <div className="spinner-container">
      <img 
        src={naruGif} 
        alt="Loading..." 
        className="spinner-image"
      />
      <p className="spinner-text">{text}</p>
    </div>
  );
};

export default Spinner;