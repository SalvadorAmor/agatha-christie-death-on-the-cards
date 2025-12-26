import React, { useState, useEffect, useRef } from "react";
import type { ChatMessage } from "../services/ChatService";
import ChatService from "../services/ChatService";

type Props = {
  messages: ChatMessage[];
  onClose: () => void;
  myPlayerId: number;
  gameId: number;
};

export default function GameChat({ messages, onClose, myPlayerId, gameId }: Props) {
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    try {
      await ChatService.create({ game_id: gameId, owner_id: myPlayerId, content: newMessage });
      setNewMessage("");
    } catch (error) {
      console.error("Error enviando mensaje:", error);
    }
  };

return (
  <div className="fixed right-0 bottom-0 h-1/2 w-80 bg-[#230812] text-white flex flex-col z-50 rounded-tl-2xl">
    <div className="flex items-center justify-between px-4 py-2 border-b border-white/20">
      <h2 className="font-bold text-base">Chat & Eventos</h2>
      <button
        onClick={onClose}
        className="text-white/70 hover:text-[#bb8512] cursor-pointer"
      >
        Cerrar ✕
      </button>
    </div>
    <div className="flex-1 overflow-y-auto px-4 py-2 text-sm space-y-1">
      {messages.map((msg) => {
        const isEvent = !msg.owner_name;

        const time = new Date(msg.timestamp).toLocaleTimeString("es-AR", {
          timeZone: "America/Argentina/Buenos_Aires",
          hour: "2-digit",
          minute: "2-digit",
        });

        return isEvent ? (
          <div key={msg.id} className="text-[#bb8512] italic py-1 font-semibold">
            <span>{msg.content}</span>
          </div>
        ) : (
          <div
            key={msg.id}
            className="text-left text-white/90 break-words"
          >
            <span className="text-[#bb8512]">[{time}]{" "}</span>
            <span className="font-semibold text-white">{msg.owner_name}{": "}</span>
            <span className="text-white/80">{msg.content}</span>
          </div>
        );
      })}
      <div ref={messagesEndRef} />
    </div>
    <div className="p-3 border-t border-white/20">
      <input
        type="text"
        value={newMessage}
        onChange={(e) => setNewMessage(e.target.value)}
        placeholder="Escribí un mensaje..."
        className="w-full p-2 rounded bg-black/20 text-white placeholder-white/40 border border-white/20  text-sm"
        maxLength={100}
        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button
        onClick={sendMessage}
        className="mt-2 w-full py-2 rounded bg-white hover:bg-[#bb8512] text-black font-semibold text-sm cursor-pointer"
      >
        Enviar
      </button>
    </div>
  </div>
);
}