import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Register from "./components/Register";
import Login from "./components/Login";
import Translator from "./components/Translator";
import GameSelection from "./components/GameSelection";
import GameUserForm from "./components/GameUserForm"; // NEW
import SinhalaWordPuzzle from "./components/SinhalaWordPuzzle";
import AIAnalyticsDashboard from './components/AIAnalyticsDashboard';
import SentenceGame from './components/sentencegame';

function App() {
  return (
    <Router>
      <div>
        <nav className="bg-gray-800 p-4 flex justify-between items-center">
          <h1 className="text-white font-bold text-lg">Sinhala Sign Language</h1>
          <div className="space-x-4">
            <Link to="/" className="text-white hover:text-yellow-400">Home</Link>
            <Link to="/login" className="text-white hover:text-yellow-400">Sign In</Link>
            <Link to="/game-register" className="text-white hover:text-yellow-400">Games</Link>
            {/* <Link to="/translate" className="text-white hover:text-yellow-400">Translate</Link> */}
          </div>
        </nav>

        <div>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/translate" element={<Translator />} />
            
            {/* Game Flow */}
            <Route path="/game-register" element={<GameUserForm />} />
            <Route path="/gameselection" element={<GameSelection />} />
            <Route path="/game/puzzle" element={<SinhalaWordPuzzle />} />
            <Route path="/ai-analytics" element={<AIAnalyticsDashboard />} />
            <Route path="/game/sentence" element={<SentenceGame />} />

          </Routes>
        </div>
      </div>
    </Router>
  );
}

const HomePage = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
    <div className="text-center text-white">
      <h1 className="text-6xl font-bold mb-4">🤟 සංඥා භාෂා</h1>
      <p className="text-2xl mb-8">Sinhala Sign Language Learning Platform</p>
      <Link 
        to="/game-register" 
        className="bg-white text-purple-600 px-8 py-4 rounded-xl font-bold hover:scale-105 transition inline-block"
      >
        Start Learning 🎮
      </Link>
    </div>
  </div>
);

export default App;