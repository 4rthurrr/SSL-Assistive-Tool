import { useState } from "react";
import axios from "axios";

function Translator() {
  const [text, setText] = useState("");
  const [translated, setTranslated] = useState("");

  const handleTranslate = async () => {
    try {
      const res = await axios.get("https://api.mymemory.translated.net/get", {
        params: {
          q: text,
          langpair: "en|si", // English → Sinhala
        },
      });
      setTranslated(res.data.responseData.translatedText);
    } catch (error) {
      console.error("Error translating:", error);
    }
  };

  return (
    <div className="p-4 bg-gray-100 rounded-lg shadow-md max-w-md mx-auto">
      <h2 className="text-xl font-bold mb-4">Sinhala Translator</h2>
      
      <textarea
        className="w-full p-2 border rounded mb-2"
        rows="3"
        placeholder="Enter English text"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      
      <button
        onClick={handleTranslate}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Translate
      </button>

      {translated && (
        <div className="mt-4 p-3 bg-white border rounded">
          <p className="font-semibold">Sinhala Translation:</p>
          <p>{translated}</p>
        </div>
      )}
    </div>
  );
}

export default Translator;
