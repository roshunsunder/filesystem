import React, { useState } from "react";
import { Ping } from '@uiball/loaders'
import "./App.css";

const App = () => {
  const [inputText, setInputText] = useState("");
  const [list, setList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (event) => {
    setInputText(event.target.value);
  };

  const handleButtonClick = async (event) => {
    // Fake API call
    event.preventDefault()
    if (inputText === '') {
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8686/query', {
        method: 'POST',
        headers: {
          'Content-Type' : 'application/json'
        },
        body: JSON.stringify({"query":inputText})
      }).then(
        res => res.json()
      ).then((data => setList(data['result'])));
    } catch (error) {
      console.log(error);
    }
    setIsLoading(false);
  };

  return (
    //<div className={`app-container ${list.length > 0 ? "floating" : ""}`}>
    <div className="app-container">
      <div className={`title`}>LLM Filesystem</div>
      <div className={`input-container`}>
        <input
          type="text"
          className="input-box"
          value={inputText}
          onChange={handleInputChange}
          placeholder="Describe your file."
        />
        <button className="go-button" onClick={handleButtonClick} disabled={isLoading}>
          Go
        </button>
      </div>
      <div className="list-div">
        {isLoading ? <div className="loader"><Ping 
          size={45}
          speed={2} 
          color="white" 
          /></div> : (
          <div className="list-container">
            {list.map((item, index) => (
              <div key={index} className="list-item">
                {item}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
