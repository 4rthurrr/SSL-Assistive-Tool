import { useNavigate } from "react-router-dom";

export default function MainPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-sky-50 space-y-10">
      <h1 className="text-3xl font-bold text-sky-600">🌟 Welcome! 🌟</h1>
      <div className="flex space-x-10">
        <div
          className="cursor-pointer hover:scale-110 transition transform"
          onClick={() => navigate("/puzzle")}
        >
          <img
            src="https://whoweare.lk/wp-content/uploads/2021/09/48-8.jpg"
            alt="Game"
            className="w-40 h-40 rounded-xl shadow-lg"
          />
          <p className="text-center text-xl font-bold text-emerald-600">Games 🎮</p>
        </div>

        <div
          className="cursor-pointer hover:scale-110 transition transform"
          onClick={() => navigate("/sign")}
        >
          <img
            src="/images/ssl-icon.png"
            alt="Sinhala Sign Language"
            className="w-40 h-40 rounded-xl shadow-lg"
          />
          <p className="text-center text-xl font-bold text-sky-700">Signs ✋</p>
        </div>
      </div>
    </div>
  );
}
