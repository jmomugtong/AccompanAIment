import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<div>AccompanAIment - Home</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
