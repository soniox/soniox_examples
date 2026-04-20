import { Conversation } from "./components/conversation";

function App() {
  return (
    <div className="min-h-screen bg-linear-to-b from-[#001227] via-[#0a59bb] to-white p-4">
      <div className="max-w-4xl mx-auto flex flex-col gap-2">
        <img src="/soniox.svg" alt="Soniox Logo" className="w-24 h-auto" />

        <Conversation />
      </div>
    </div>
  );
}

export default App;
