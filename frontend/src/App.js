import React, { useState } from "react";
import "./App.css";

const App = () => {
  const [inputText, setInputText] = useState("");

  const handleInputChange = (event) => {
    setInputText(event.target.value);
  };

  const handleButtonClick = () => {
    // Call your function here with the current inputText
    console.log("Current input text:", inputText);
  };

  return (
    <div className="app-container">
      <div className="title">LLM Filesystem</div>
      <div className="input-container">
        <input
          type="text"
          className="input-box"
          value={inputText}
          onChange={handleInputChange}
          placeholder="Describe your file."
        />
        <button className="go-button" onClick={handleButtonClick}>
          Go
        </button>
      </div>
    </div>
  );
};

export default App;
