import React, { useState, useRef } from "react";

export default function App() {
  const [srcLang, setSrcLang] = useState("hi");
  const [destLang, setDestLang] = useState("en");
  const [translated, setTranslated] = useState("");
  const [original, setOriginal] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);
  const [recording, setRecording] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const languages = [
    { code: "en", name: "English" },
    { code: "hi", name: "Hindi" },
    { code: "ta", name: "Tamil" },
    { code: "te", name: "Telugu" },
    { code: "kn", name: "Kannada" },
    { code: "ml", name: "Malayalam" },
    { code: "mr", name: "Marathi" },
    { code: "bn", name: "Bengali" },
    { code: "gu", name: "Gujarati" },
  ];

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    setRecording(true);
    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      audioChunksRef.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      console.log("Audio blob size:", blob.size, "bytes");
      
      const formData = new FormData();
      formData.append("src_lang", srcLang);
      formData.append("dest_lang", destLang);
      formData.append("audio_data", blob, "speech.wav");

      console.log("Sending translation request...");
      console.log("Source language:", srcLang);
      console.log("Destination language:", destLang);

      try {
        const res = await fetch("http://localhost:5001/translate-voice", {
          method: "POST",
          body: formData,
        });

        console.log("Response status:", res.status);
        
        if (!res.ok) {
          const errorText = await res.text();
          console.error("Server error:", errorText);
          return;
        }

        const data = await res.json();
        console.log("Translation response:", data);
        
        setOriginal(data.original_text);
        setTranslated(data.translated_text);
        if (data.audio_base64) {
          setAudioUrl("data:audio/mp3;base64," + data.audio_base64);
        }
      } catch (error) {
        console.error("Error translating audio:", error);
      }
    };

    mediaRecorderRef.current.start();
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <h1 className="text-3xl font-bold mb-6 text-blue-600">
        🎧 Multilingual Voice Translator
      </h1>

      <div className="flex gap-4 mb-6">
        <select
          value={srcLang}
          onChange={(e) => setSrcLang(e.target.value)}
          className="border p-2 rounded"
        >
          {languages.map((l) => (
            <option key={l.code} value={l.code}>
              {l.name}
            </option>
          ))}
        </select>
        <span>➡️</span>
        <select
          value={destLang}
          onChange={(e) => setDestLang(e.target.value)}
          className="border p-2 rounded"
        >
          {languages.map((l) => (
            <option key={l.code} value={l.code}>
              {l.name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={recording ? stopRecording : startRecording}
        className={`px-6 py-3 rounded text-white font-semibold ${
          recording ? "bg-red-500" : "bg-green-500"
        }`}
      >
        {recording ? "🛑 Stop Recording" : "🎙️ Start Recording"}
      </button>

      <div className="mt-6 w-full max-w-md text-center">
        {original && (
          <p className="text-gray-600 mb-2">
            <strong>Original:</strong> {original}
          </p>
        )}
        {translated && (
          <p className="text-gray-800 text-lg">
            <strong>Translated:</strong> {translated}
          </p>
        )}
        {audioUrl && (
          <audio className="mt-4" controls src={audioUrl}>
            Your browser does not support the audio element.
          </audio>
        )}
      </div>
    </div>
  );
}
