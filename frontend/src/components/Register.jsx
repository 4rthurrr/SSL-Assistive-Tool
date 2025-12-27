import { useState } from "react";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", password: "", age: "" });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:5000/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      alert("🎉 Registered Successfully!");
      console.log(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-r from-pink-300 via-purple-300 to-blue-300">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-lg p-6 w-80 space-y-4 text-center"
      >
        <h1 className="text-2xl font-bold text-purple-600">🧸 Register</h1>

        <input
          type="text"
          name="name"
          placeholder="👤 Name"
          value={form.name}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-400"
          required
        />

        <input
          type="email"
          name="email"
          placeholder="📧 Email"
          value={form.email}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-400"
          required
        />

        <input
          type="password"
          name="password"
          placeholder="🔑 Password"
          value={form.password}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-400"
          required
        />

        <input
          type="number"
          name="age"
          placeholder="🎂 Age"
          value={form.age}
          onChange={handleChange}
          className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-400"
          required
        />

        <button className="bg-purple-500 text-white py-2 px-4 rounded-xl w-full hover:bg-purple-600 transition">
          Register 🚀
        </button>
      </form>
    </div>
  );
}
