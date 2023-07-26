import React, { useState } from "react";
import "./App.css";

const App = () => {
  const [inputText, setInputText] = useState("");
  const [list, setList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFloating, setIsFloating] = useState(false);

  const handleInputChange = (event) => {
    setInputText(event.target.value);
  };

  const handleButtonClick = () => {
    // Fake API call
    setIsLoading(true);
    setList([])
    setIsLoading(false);
    setIsFloating(true);
  };

  return (
    //<div className={`app-container ${list.length > 0 ? "floating" : ""}`}>
    <div className="app-container">
      <div className={`title ${isFloating ? "floating" : ""}`}>LLM Filesystem</div>
      <div className={`input-container ${isFloating ? "floating" : ""}`}>
        <input
          type="text"
          className="input-box"
          value={inputText}
          onChange={handleInputChange}
          placeholder="Describe your file."
        />
        <button className="go-button" onClick={handleButtonClick} disabled={isLoading}>
          {isLoading ? "Loading..." : "Go"}
        </button>
      </div>
      {list.length > 0 && (
        <div className="list-container">
          {list.map((item, index) => (
            <div key={index} className="list-item">
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default App;
