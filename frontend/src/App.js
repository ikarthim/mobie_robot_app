import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import RobotController from "./components/RobotController";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RobotController />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;