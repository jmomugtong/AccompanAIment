import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Home } from "./pages/Home";
import { Generate } from "./pages/Generate";
import { History } from "./pages/History";
import { Feedback } from "./pages/Feedback";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/history" element={<History />} />
          <Route path="/feedback" element={<Feedback />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
