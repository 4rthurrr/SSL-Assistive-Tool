import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Register from "./components/Register";
import Login from "./components/Login";
import Translator from "./components/Translator";
import GameSelection from "./components/GameSelection";
import GameUserForm from "./components/GameUserForm";
import SinhalaWordPuzzle from "./components/SinhalaWordPuzzle";
import AIAnalyticsDashboard from './components/AIAnalyticsDashboard';
import SentenceGame from './components/sentencegame';
import SSLTranslator from './App.js';

function App() {
  return (
    <Router>
      <div>
        <nav className="bg-gray-800 p-4 flex justify-between items-center">
          <Link to="/" className="text-white font-bold text-lg">🤟 සංඥා භාෂා</Link>
          <div className="space-x-4">
            <Link to="/" className="text-white hover:text-yellow-400">Home</Link>
            <Link to="/ssl-translator" className="text-white hover:text-yellow-400">✨ Translator</Link>
            <Link to="/game-register" className="text-white hover:text-yellow-400">🎮 Games</Link>
            <Link to="/login" className="text-white hover:text-yellow-400">Sign In</Link>
          </div>
        </nav>

        <div>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/translate" element={<Translator />} />
            
            {/* SSL Translator */}
            <Route path="/ssl-translator" element={<SSLTranslator />} />

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
  <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col items-center justify-center gap-10 p-8">
    <div className="text-center text-white">
      <h1 className="text-6xl font-bold mb-3">🤟 සංඥා භාෂා</h1>
      <p className="text-2xl opacity-90">Sinhala Sign Language Learning Platform</p>
    </div>

    <div className="flex flex-col sm:flex-row gap-6">
      {/* Translator Card */}
      <Link
        to="/ssl-translator"
        className="bg-white rounded-2xl shadow-xl p-8 flex flex-col items-center gap-4 hover:scale-105 transition cursor-pointer w-64"
      >
        <span className="text-6xl">✨</span>
        <h2 className="text-2xl font-bold text-purple-700">SSL Translator</h2>
        <p className="text-gray-500 text-center text-sm">Type Sinhala text and watch it signed by an avatar</p>
        <span className="bg-purple-600 text-white px-6 py-2 rounded-full font-semibold mt-2">Open →</span>
      </Link>

      {/* Games Card */}
      <Link
        to="/game-register"
        className="bg-white rounded-2xl shadow-xl p-8 flex flex-col items-center gap-4 hover:scale-105 transition cursor-pointer w-64"
      >
        <span className="text-6xl">🎮</span>
        <h2 className="text-2xl font-bold text-green-700">Learning Games</h2>
        <p className="text-gray-500 text-center text-sm">Practice sign language with fun interactive games</p>
        <span className="bg-green-600 text-white px-6 py-2 rounded-full font-semibold mt-2">Play →</span>
      </Link>
    </div>
  </div>
);

export default App;